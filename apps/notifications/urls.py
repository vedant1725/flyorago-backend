from django.urls import path
from .views import NotificationListView, NotificationMarkReadAllView, NotificationMarkReadSingleView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('read', NotificationMarkReadAllView.as_view(), name='notification_read_all'),
    path('read/', NotificationMarkReadAllView.as_view(), name='notification_read_all_slash'),
    path('read-all/', NotificationMarkReadAllView.as_view(), name='notification_read_all_hyphen'),
    path('read/<int:pk>', NotificationMarkReadSingleView.as_view(), name='notification_read_single'),
    path('read/<int:pk>/', NotificationMarkReadSingleView.as_view(), name='notification_read_single_slash'),
    path('<int:pk>/read', NotificationMarkReadSingleView.as_view(), name='notification_read_single_alt'),
    path('<int:pk>/read/', NotificationMarkReadSingleView.as_view(), name='notification_read_single_alt_slash'),
]

