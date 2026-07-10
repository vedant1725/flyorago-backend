from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema

from .models import FAQ, Ticket, TicketReply
from .serializers import FAQSerializer, TicketSerializer, TicketReplySerializer
from common.responses import success_response, failure_response

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
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]
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

