from django.urls import path
from .views import BookingListCreateView, BookingDetailView, BookingActionView

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking_list_create'),
    path('<int:pk>', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/action', BookingActionView.as_view(), name='booking_action'),
]
