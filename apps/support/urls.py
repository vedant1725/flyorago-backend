from django.urls import path
from .views import FAQListView, TicketListCreateView, TicketDetailView, TicketReplyCreateView

urlpatterns = [
    path('faqs', FAQListView.as_view(), name='faq_list'),
    path('tickets', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:ticket_id>/reply', TicketReplyCreateView.as_view(), name='ticket_reply_create'),
]
