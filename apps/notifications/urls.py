from django.urls import path
from .views import NotificationListView, NotificationMarkReadAllView, NotificationMarkReadSingleView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('read', NotificationMarkReadAllView.as_view(), name='notification_read_all'),
    path('read/<int:pk>', NotificationMarkReadSingleView.as_view(), name='notification_read_single'),
]

