from django.urls import path
from .views import (
    FAQListView, TicketListCreateView, TicketDetailView, TicketReplyCreateView,
    DisputeListCreateView, AdminDisputeListView, AdminDisputeActionView,
    ContactMessageCreateView, AdminContactMessageListView, AdminContactMessageDetailView
)

urlpatterns = [
    path('faqs', FAQListView.as_view(), name='faq_list'),
    path('tickets', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:ticket_id>/reply', TicketReplyCreateView.as_view(), name='ticket_reply_create'),
    path('disputes', DisputeListCreateView.as_view(), name='dispute_list_create'),
    path('admin/disputes', AdminDisputeListView.as_view(), name='admin_dispute_list'),
    path('admin/disputes/<int:pk>/action', AdminDisputeActionView.as_view(), name='admin_dispute_action'),
    path('contact', ContactMessageCreateView.as_view(), name='contact_create'),
    path('admin/contact-messages', AdminContactMessageListView.as_view(), name='admin_contact_list'),
    path('admin/contact-messages/<int:pk>', AdminContactMessageDetailView.as_view(), name='admin_contact_detail'),
]
