from django.urls import path
from .views import (
    PaymentIntentCreateView, PaymentIntentConfirmView, InvoiceDetailView,
    SystemSettingsView, AdminSystemSettingsUpdateView
)

urlpatterns = [
    path('intents', PaymentIntentCreateView.as_view(), name='payment_intent_create'),
    path('intents/<int:pk>/confirm', PaymentIntentConfirmView.as_view(), name='payment_intent_confirm'),
    path('invoice/<int:booking_id>', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('settings', SystemSettingsView.as_view(), name='system_settings_get'),
    path('settings/', SystemSettingsView.as_view(), name='system_settings_get_slash'),
    path('admin/settings', AdminSystemSettingsUpdateView.as_view(), name='admin_system_settings_post'),
    path('admin/settings/', AdminSystemSettingsUpdateView.as_view(), name='admin_system_settings_post_slash'),
]
