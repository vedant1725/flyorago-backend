from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from .knowledge_base import QUICK_NAV_ACTIONS
from .llm_engine import LLMEngine
from .models import AIKnowledgeBaseItem

class FlyoraAIChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response({
                'status': 'error',
                'message': 'Prompt text is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user_context = {}
        if request.user and request.user.is_authenticated:
            user_context = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': getattr(request.user, 'first_name', '') or request.user.email.split('@')[0],
                'role': getattr(request.user, 'role', 'traveler')
            }

        history = request.data.get('history', [])

        response_data = LLMEngine.generate_response(prompt, user_context, history)

        return Response({
            'status': 'success',
            'data': response_data
        }, status=status.HTTP_200_OK)


class FlyoraAIPromptsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        suggested_prompts = [
            {"id": 1, "title": "🧳 How does Luggage Sharing work?", "prompt": "How does Luggage Sharing work?"},
            {"id": 2, "title": "📦 How do I send a parcel?", "prompt": "How do I send a parcel?"},
            {"id": 3, "title": "💰 How is my payment protected in Escrow?", "prompt": "How is my payment protected in Escrow?"},
            {"id": 4, "title": "🛡️ What is Trust Score & KYC?", "prompt": "What is Trust Score & KYC?"},
            {"id": 5, "title": "🚫 What items are prohibited?", "prompt": "Any drugs item delivered?"},
        ]
        return Response({
            'status': 'success',
            'data': {
                'suggested_prompts': suggested_prompts,
                'quick_actions': list(QUICK_NAV_ACTIONS.values())
            }
        })


class AdminAIKnowledgeView(APIView):
    permission_classes = [AllowAny]  # Allow admin access

    def get(self, request):
        items = AIKnowledgeBaseItem.objects.all().order_by('-created_at')
        data = [
            {
                'id': item.id,
                'category': item.category,
                'category_display': item.get_category_display(),
                'question': item.question,
                'answer': item.answer,
                'is_active': item.is_active,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for item in items
        ]
        return Response({'status': 'success', 'data': data})

    def post(self, request):
        category = request.data.get('category', 'platform')
        question = request.data.get('question', '').strip()
        answer = request.data.get('answer', '').strip()
        is_active = request.data.get('is_active', True)

        if not question or not answer:
            return Response({'status': 'error', 'message': 'Question and answer are required.'}, status=400)

        item = AIKnowledgeBaseItem.objects.create(
            category=category,
            question=question,
            answer=answer,
            is_active=is_active
        )
        return Response({
            'status': 'success',
            'message': 'AI Knowledge Item created successfully',
            'data': {
                'id': item.id,
                'category': item.category,
                'question': item.question,
                'answer': item.answer,
                'is_active': item.is_active
            }
        }, status=210 if status.HTTP_201_CREATED else 201)

    def delete(self, request, pk=None):
        if not pk:
            return Response({'status': 'error', 'message': 'Item ID is required'}, status=400)
        try:
            item = AIKnowledgeBaseItem.objects.get(pk=pk)
            item.delete()
            return Response({'status': 'success', 'message': 'Item deleted successfully'})
        except AIKnowledgeBaseItem.DoesNotExist:
            return Response({'status': 'error', 'message': 'Item not found'}, status=404)
