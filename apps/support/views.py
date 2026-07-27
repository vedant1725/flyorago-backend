from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser

from .models import FAQ, Ticket, TicketReply, Dispute, DisputeImage
from .serializers import FAQSerializer, TicketSerializer, TicketReplySerializer, DisputeSerializer, AdminDisputeSerializer
from common.responses import success_response, failure_response
from common.permissions import IsKYCApproved
from wallet.models import Wallet, Transaction

class FAQListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FAQSerializer

    def get_queryset(self):
        category = self.request.query_params.get('category')
        q = self.request.query_params.get('q')
        
        queryset = FAQ.objects.all()
        if category:
            queryset = queryset.filter(category=category)
        if q:
            queryset = queryset.filter(question__icontains=q)
            
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="FAQs retrieved successfully")

class TicketListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).prefetch_related('replies')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Support tickets list retrieved")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save(user=request.user)
            full_data = TicketSerializer(ticket).data
            return success_response(data=full_data, message="Support ticket created successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to open support ticket")

class TicketDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Ticket details retrieved")

class TicketReplyCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = TicketReplySerializer

    @extend_schema(request=TicketReplySerializer, responses={201: TicketReplySerializer})
    @transaction.atomic
    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
        serializer = TicketReplySerializer(data=request.data)
        if serializer.is_valid():
            reply = serializer.save(
                ticket=ticket,
                sender=request.user
            )
            # Reopen or update ticket status
            if ticket.status in ['Resolved', 'Closed']:
                ticket.status = 'Open'
                ticket.save()
            return success_response(data=TicketReplySerializer(reply).data, message="Reply posted successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to post ticket reply")

class DisputeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DisputeSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Dispute.objects.filter(raised_by=self.request.user).prefetch_related('images')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Disputes retrieved successfully")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check 7 days limit
            booking = serializer.validated_data['booking']
            from django.utils import timezone
            import datetime
            if booking.status != 'DELIVERED':
                return failure_response(message="Dispute can only be raised for delivered bookings.")
            # Assume delivered_at exists. If not, just check 7 days from updated_at
            if (timezone.now() - booking.updated_at).days > 7:
                return failure_response(message="Disputes can only be raised within 7 days of delivery.")
                
            dispute = serializer.save(raised_by=request.user)
            
            # Save images
            for file in request.FILES.getlist('images'):
                DisputeImage.objects.create(dispute=dispute, image=file)
                
            booking.status = 'DISPUTED'
            booking.save()
            
            # Socket notification
            from bookings.services import BookingWorkflowService
            BookingWorkflowService.trigger_websocket_notification(booking, "dispute_raised", "A dispute has been raised for this booking.")
            
            return success_response(data=DisputeSerializer(dispute).data, message="Dispute raised successfully.", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to raise dispute.")

class AdminDisputeListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AdminDisputeSerializer
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        queryset = Dispute.objects.all().prefetch_related('images', 'booking', 'raised_by').order_by('-created_at')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="All disputes retrieved.")

class AdminDisputeActionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, pk):
        action = request.data.get('action')
        reason = request.data.get('reason')
        dispute = get_object_or_404(Dispute, pk=pk)
        booking = dispute.booking

        if action not in ['APPROVE', 'REJECT', 'REQUEST_EVIDENCE']:
            return failure_response(message="Invalid action. Must be APPROVE, REJECT, or REQUEST_EVIDENCE.")

        if action == 'APPROVE':
            dispute.status = 'Resolved'
            dispute.resolution = f"Approved: {reason}"
            
            # Financial Logic (Deduct 20% from Traveler and give to Sender)
            penalty_amount = Decimal(str(float(booking.reward) * 0.20))
            
            # Penalty Traveler 20%
            traveler_wallet, _ = Wallet.objects.get_or_create(user=booking.traveler)
            traveler_wallet.balance_available -= penalty_amount
            traveler_wallet.save()
            Transaction.objects.create(
                wallet=traveler_wallet,
                amount=penalty_amount,
                type='Withdrawal',
                status='Completed',
                description="Dispute Penalty (20% of earning)",
                reference_id=f"PENALTY_DISPUTE_{dispute.id}"
            )
            
            # Credit Sender 20%
            sender_wallet, _ = Wallet.objects.get_or_create(user=booking.sender)
            sender_wallet.balance_available += penalty_amount
            sender_wallet.save()
            Transaction.objects.create(
                wallet=sender_wallet,
                amount=penalty_amount,
                type='Refund',
                status='Completed',
                description="Dispute Compensation",
                reference_id=f"COMP_DISPUTE_{dispute.id}"
            )
            
            booking.status = 'DISPUTE_RESOLVED'
            
        elif action == 'REJECT':
            dispute.status = 'Closed'
            dispute.resolution = f"Rejected: {reason}"
            booking.status = 'DISPUTE_REJECTED'
            
        elif action == 'REQUEST_EVIDENCE':
            dispute.status = 'Under Review'
            dispute.resolution = f"Evidence Requested: {reason}"

        dispute.save()
        booking.save()
        
        # Socket notification
        from bookings.services import BookingWorkflowService
        notification_msg = "Your dispute has been approved! You received a 20% compensation." if action == 'APPROVE' else f"Dispute status changed to {dispute.status}"
        BookingWorkflowService.trigger_websocket_notification(booking, "dispute_updated", notification_msg)

        return success_response(data=AdminDisputeSerializer(dispute).data, message=f"Dispute {action.lower()}d successfully.")
