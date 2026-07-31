from django.urls import path
from .views import FlyoraAIChatView, FlyoraAIPromptsView, AdminAIKnowledgeView

urlpatterns = [
    path('chat/', FlyoraAIChatView.as_view(), name='flyora_ai_chat'),
    path('prompts/', FlyoraAIPromptsView.as_view(), name='flyora_ai_prompts'),
    path('admin/faqs/', AdminAIKnowledgeView.as_view(), name='admin_ai_knowledge'),
    path('admin/faqs/<int:pk>/', AdminAIKnowledgeView.as_view(), name='admin_ai_knowledge_detail'),
]
