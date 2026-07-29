from rest_framework import generics, views, status, permissions
from rest_framework import serializers
from django.contrib.auth import get_user_model
from common.responses import success_response, failure_response

# Models
from trips.models import Trip
from bookings.models import Booking
from profiles.models import Profile
from support.models import Dispute

# Serializers
from users.serializers import UserSerializer
from trips.serializers import TripSerializer
from bookings.serializers import BookingSerializer
from profiles.serializers import ProfileSerializer

User = get_user_model()

class AdminDisputeSerializer(serializers.ModelSerializer):
    raised_by_email = serializers.CharField(source='raised_by.email', read_only=True)
    
    class Meta:
        model = Dispute
        fields = '__all__'


class BaseAdminListView(generics.ListAPIView):
    """
    Base view to enforce IsAuthenticated and wrap responses in
    the project's standard success_response format.
    """
    permission_classes = [permissions.IsAuthenticated]
    message_text = "Data retrieved successfully"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message=self.message_text)


class AdminUserListView(BaseAdminListView):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    message_text = "Users fetched successfully for Admin"


class AdminTripListView(BaseAdminListView):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    message_text = "Trips fetched successfully for Admin"


class AdminBookingListView(BaseAdminListView):
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    message_text = "Bookings fetched successfully for Admin"


class AdminTrustListView(BaseAdminListView):
    queryset = Profile.objects.all().order_by('-id')
    serializer_class = ProfileSerializer
    message_text = "Profiles fetched successfully for Admin Trust Check"


class AdminDisputeListView(BaseAdminListView):
    queryset = Dispute.objects.all().order_by('-created_at')
    serializer_class = AdminDisputeSerializer
    message_text = "Disputes fetched successfully for Admin"


class AdminStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        data = {
            "total_users": User.objects.count(),
            "total_trips": Trip.objects.count(),
            "total_bookings": Booking.objects.count(),
            "total_disputes": Dispute.objects.count()
        }
        return success_response(data=data, message="Stats fetched successfully")

class AdminChartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Basic mocked chart data matching common expectations
        data = {
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "bookings": [12, 19, 3, 5, 2, 3, 10, 15, 20, 30, 25, 40]
        }
        return success_response(data=data, message="Chart data fetched successfully")
