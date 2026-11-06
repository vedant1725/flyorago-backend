from django.urls import path
from .views import (
    NotificationListView, 
    NotificationMarkReadAllView, 
    NotificationMarkReadSingleView,
    NotificationDeleteSingleView,
    NotificationClearAllView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('read', NotificationMarkReadAllView.as_view(), name='notification_read_all'),
    path('read/', NotificationMarkReadAllView.as_view(), name='notification_read_all_slash'),
    path('read-all/', NotificationMarkReadAllView.as_view(), name='notification_read_all_hyphen'),
    path('read/<int:pk>', NotificationMarkReadSingleView.as_view(), name='notification_read_single'),
    path('read/<int:pk>/', NotificationMarkReadSingleView.as_view(), name='notification_read_single_slash'),
    path('<int:pk>/read', NotificationMarkReadSingleView.as_view(), name='notification_read_single_alt'),
    path('<int:pk>/read/', NotificationMarkReadSingleView.as_view(), name='notification_read_single_alt_slash'),
    path('<int:pk>/', NotificationDeleteSingleView.as_view(), name='notification_delete_single'),
    path('<int:pk>', NotificationDeleteSingleView.as_view(), name='notification_delete_single_noslash'),
    path('clear/', NotificationClearAllView.as_view(), name='notification_clear_all'),
    path('clear', NotificationClearAllView.as_view(), name='notification_clear_all_noslash'),
]
