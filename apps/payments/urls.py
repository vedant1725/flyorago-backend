from django.urls import path
from .views import PaymentIntentCreateView, PaymentIntentConfirmView, InvoiceDetailView

urlpatterns = [
    path('intents', PaymentIntentCreateView.as_view(), name='payment_intent_create'),
    path('intents/<int:pk>/confirm', PaymentIntentConfirmView.as_view(), name='payment_intent_confirm'),
    path('invoice/<int:booking_id>', InvoiceDetailView.as_view(), name='invoice_detail'),
]
