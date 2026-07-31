from django.urls import path
from .views import (
    FAQListView, TicketListCreateView, TicketDetailView, TicketReplyCreateView,
    DisputeListCreateView, AdminDisputeListView, AdminDisputeActionView,
    ContactMessageCreateView, AdminContactMessageListView, AdminContactMessageDetailView
)

urlpatterns = [
    path('faqs', FAQListView.as_view(), name='faq_list'),
    path('faqs/', FAQListView.as_view(), name='faq_list_slash'),
    path('tickets', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('tickets/', TicketListCreateView.as_view(), name='ticket_list_create_slash'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail_slash'),
    path('tickets/<int:ticket_id>/reply', TicketReplyCreateView.as_view(), name='ticket_reply_create'),
    path('tickets/<int:ticket_id>/reply/', TicketReplyCreateView.as_view(), name='ticket_reply_create_slash'),
    path('disputes', DisputeListCreateView.as_view(), name='dispute_list_create'),
    path('disputes/', DisputeListCreateView.as_view(), name='dispute_list_create_slash'),
    path('admin/disputes', AdminDisputeListView.as_view(), name='admin_dispute_list'),
    path('admin/disputes/', AdminDisputeListView.as_view(), name='admin_dispute_list_slash'),
    path('admin/disputes/<int:pk>/action', AdminDisputeActionView.as_view(), name='admin_dispute_action'),
    path('admin/disputes/<int:pk>/action/', AdminDisputeActionView.as_view(), name='admin_dispute_action_slash'),
    path('contact', ContactMessageCreateView.as_view(), name='contact_create'),
    path('admin/contact-messages', AdminContactMessageListView.as_view(), name='admin_contact_list'),
    path('admin/contact-messages/<int:pk>', AdminContactMessageDetailView.as_view(), name='admin_contact_detail'),
]
