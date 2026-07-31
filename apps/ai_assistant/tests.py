import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from apps.ai_assistant.models import AIKnowledgeBaseItem
from apps.ai_assistant.llm_engine import LLMEngine
from apps.ai_assistant.knowledge_base import retrieve_knowledge_context, detect_language

class FlyoraAIChatbotTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chat_url = reverse('flyora_ai_chat')
        self.admin_faq_url = reverse('admin_ai_knowledge')
        
        # Create sample DB FAQ
        self.custom_faq = AIKnowledgeBaseItem.objects.create(
            category='payments',
            question='What is the refund timeline for cancelled trips?',
            answer='If a trip is cancelled, funds are refunded 100% back to the sender within 24 hours.',
            is_active=True
        )

    def test_detect_language(self):
        """Test language detection for English, Gujarati, and Hindi."""
        self.assertEqual(detect_language("How does luggage sharing work?"), "en")
        self.assertEqual(detect_language("Kem cho bhai, su che?"), "gu")
        self.assertEqual(detect_language("Kaise kaam karta hai yeh?"), "hi")

    def test_retrieve_knowledge_context(self):
        """Verify RAG context assembler includes policies and admin FAQs."""
        db_items = list(AIKnowledgeBaseItem.objects.filter(is_active=True).values('category', 'question', 'answer', 'is_active'))
        context = retrieve_knowledge_context("refund timeline", None, db_items)
        
        self.assertIn("OFFICIAL FLYORAGO POLICIES", context)
        self.assertIn("PROHIBITED ITEMS", context)
        self.assertIn("PRESCRIPTION MEDICINES", context)
        self.assertIn("What is the refund timeline for cancelled trips?", context)

    def test_chat_api_missing_prompt(self):
        """Test 400 error when prompt is empty."""
        response = self.client.post(self.chat_url, data={}, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('urllib.request.urlopen')
    def test_gemini_integration_success(self, mock_urlopen):
        """Test successful Gemini API response generation and reasoning."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "FlyoraGo Escrow protects payments by locking funds until 6-digit OTP confirmation."
                    }]
                }
            }]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with override_settings(AI_PROVIDER='gemini', GEMINI_API_KEY='test_api_key'):
            res = LLMEngine.generate_response("How does Escrow protect my payment?", None, [])
            
            self.assertEqual(res['provider'], 'gemini')
            self.assertIn("Escrow protects payments", res['text'])
            self.assertTrue(len(res['actions']) > 0)

    @patch('urllib.request.urlopen')
    def test_gemini_api_key_not_exposed(self, mock_urlopen):
        """Test Security Requirement (Step 10): API key must never appear in API responses or logs."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Prescription medicines require doctor prescription and sealed packaging."
                    }]
                }
            }]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        secret_key = "AQ.Ab8RN6JMZXeeo1pGQBiXG7ffo6BMk72xnWmgpy1gcjxEX9NUBg"
        with override_settings(AI_PROVIDER='gemini', GEMINI_API_KEY=secret_key):
            response = self.client.post(self.chat_url, data={"prompt": "Can I send pills?"}, format='json')
            self.assertEqual(response.status_code, 200)
            res_str = json.dumps(response.json())
            self.assertNotIn(secret_key, res_str)

    def test_fallback_engine_policy_preservation(self):
        """Test knowledge base fallback engine maintains 100% existing policies."""
        with override_settings(AI_PROVIDER='knowledge_base'):
            # Prohibited items check
            res1 = LLMEngine.generate_response("Can I carry drugs or weapons?", None, [])
            self.assertIn("Prohibited Items Policy", res1['text'])
            self.assertIn("Zero-Tolerance", res1['text'])

            # Prescription medicines check
            res2 = LLMEngine.generate_response("Can I send prescription medicine?", None, [])
            self.assertIn("Prescription Medicine Transport Policy", res2['text'])
            self.assertIn("Valid Doctor Prescription", res2['text'])

            # How it works check
            res3 = LLMEngine.generate_response("How does FlyoraGo work?", None, [])
            self.assertIn("Luggage Sharing", res3['text'])

    def test_multi_turn_history_in_fallback(self):
        """Test Step 8: Never show welcome menu after the first message when conversation history exists."""
        with override_settings(AI_PROVIDER='knowledge_base'):
            history = [
                {"sender": "user", "text": "Hi"},
                {"sender": "ai", "text": "I am Flyora AI..."}
            ]
            res = LLMEngine.generate_response("asdfghjkl random string", None, history)
            self.assertNotIn("How can I assist you today?\n\n1. **How Luggage Sharing Works**", res['text'])
            self.assertIn("Could you please clarify your question", res['text'])

    def test_admin_faq_crud(self):
        """Test Admin AI Settings / FAQ CRUD functionality."""
        # Get list
        get_res = self.client.get(self.admin_faq_url)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(len(get_res.json()['data']), 1)

        # Create new FAQ
        create_res = self.client.post(self.admin_faq_url, data={
            "category": "security",
            "question": "Is passport verification safe?",
            "answer": "Yes, passport verification is 256-bit encrypted.",
            "is_active": True
        }, format='json')
        self.assertIn(create_res.status_code, [200, 201, 210])


        # Delete FAQ
        item_id = create_res.json()['data']['id']
        del_res = self.client.delete(f"{self.admin_faq_url}{item_id}/")
        self.assertEqual(del_res.status_code, 200)

    def test_trust_and_safety_intent_questions(self):
        """Test user-requested TRUST_AND_SAFETY intent detection scenarios."""
        with override_settings(AI_PROVIDER='knowledge_base'):
            # Input 1: Stranger trust question
            res1 = LLMEngine.generate_response("Why should I trust a stranger traveller with my parcel?", None, [])
            self.assertIn("Trust, Safety & Fraud Protection Architecture", res1['text'])
            self.assertIn("Passport & ID KYC", res1['text'])
            self.assertIn("Protected Escrow Vault", res1['text'])

            # Input 2: Non-delivery question
            res2 = LLMEngine.generate_response("What happens if traveller does not deliver?", None, [])
            self.assertIn("Trust, Safety & Fraud Protection Architecture", res2['text'])
            self.assertIn("Escrow Vault", res2['text'])

    @patch('urllib.request.urlopen')
    def test_two_tier_hybrid_routing(self, mock_urlopen):
        """Test Tier 1 direct match preservation vs Tier 2 Gemini intelligence fallback."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "FlyoraGo is safer than traditional couriers because of 5 security layers..."
                    }]
                }
            }]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with override_settings(AI_PROVIDER='gemini', GEMINI_API_KEY='test_key'):
            # 1. Direct Policy Match -> Handled by Tier 1 (Knowledge Base)
            res_tier1 = LLMEngine.generate_response("Can I send prescription medicine?", None, [])
            self.assertEqual(res_tier1['provider'], 'knowledge_base')
            self.assertIn("Prescription Medicine Transport Policy", res_tier1['text'])

            # 2. Complex Reasoning Match -> Handled by Tier 2 (Gemini RAG Layer)
            res_tier2 = LLMEngine.generate_response("Is FlyoraGo safer than normal courier?", None, [])
            self.assertEqual(res_tier2['provider'], 'gemini')
            self.assertIn("safer than traditional couriers", res_tier2['text'])


