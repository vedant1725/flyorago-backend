from django.urls import path
from .views import ShipmentListCreateView, ShipmentDetailView, ShipmentUpdateStatusView

urlpatterns = [
    path('', ShipmentListCreateView.as_view(), name='shipment_list_create'),
    path('<int:pk>', ShipmentDetailView.as_view(), name='shipment_detail'),
    path('<int:pk>/status', ShipmentUpdateStatusView.as_view(), name='shipment_status_update'),
]
