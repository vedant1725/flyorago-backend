from rest_framework import generics, permissions, status, views, serializers
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from .models import Notification
from .serializers import NotificationSerializer
from common.responses import success_response, failure_response

class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Notifications retrieved successfully")

class NotificationActionResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class NotificationMarkReadAllView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(request=None, responses={200: NotificationActionResponseSerializer})
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read")

class NotificationMarkReadSingleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(request=None, responses={200: NotificationActionResponseSerializer})
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return success_response(message="Notification marked as read")

