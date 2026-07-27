"""
Configurable LLM Provider Abstraction & Reasoning Engine for Flyora AI
Supports multi-turn conversation history, intent understanding, direct answers, and provider abstraction (OpenAI, Gemini, Claude, or KB Fallback).
"""

import os
import json
import urllib.request
import urllib.error
from django.conf import settings
from .knowledge_base import classify_intent_and_respond as generate_kb_response, QUICK_NAV_ACTIONS

SYSTEM_PROMPT = """You are Flyora AI, an intelligent, intent-aware AI assistant for FlyoraGo — a peer-to-peer travel logistics marketplace.
Your Guidelines:
1. UNDERSTAND INTENT: Analyze the user's question directly. Do not output generic marketing or fluff.
2. DIRECT & FACTUAL:
   - If asked about earning, explain the exact earning & escrow release workflow.
   - If asked about fraud, explain identity KYC, physical parcel photo inspection, 100% escrow vault hold, and 6-digit OTP cryptographic release.
   - If asked about traveler income, explain how travelers monetize unused baggage capacity and when escrow funds are transferred to their wallet.
   - If the user's question is ambiguous or unclear, ask a helpful follow-up question.
3. CONVERSATIONAL & DYNAMIC: Maintain context across conversation history. Respond like ChatGPT with deep knowledge of FlyoraGo."""


class LLMEngine:
    @staticmethod
    def get_provider() -> str:
        return getattr(settings, 'AI_PROVIDER', os.getenv('AI_PROVIDER', 'knowledge_base')).lower()

    @classmethod
    def generate_response(cls, prompt_text: str, user_context: dict = None, history: list = None) -> dict:
        provider = cls.get_provider()
        
        # 1. Try Gemini API
        if provider == 'gemini':
            api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
            if api_key:
                res = cls._call_gemini(prompt_text, api_key, user_context, history)
                if res:
                    return res

        # 2. Try OpenAI API
        elif provider == 'openai':
            api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            if api_key:
                res = cls._call_openai(prompt_text, api_key, user_context, history)
                if res:
                    return res

        # 3. Try Anthropic Claude API
        elif provider == 'claude':
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY', ''))
            if api_key:
                res = cls._call_claude(prompt_text, api_key, user_context, history)
                if res:
                    return res

        # 4. Fallback to Intent-Aware Knowledge Base Engine
        return cls._call_fallback(prompt_text, user_context, history)

    @classmethod
    def _call_gemini(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None) -> dict:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            contents = []
            if history and isinstance(history, list):
                for h in history[-6:]:
                    role = "user" if h.get("sender") == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": h.get("text", "")}]})
            contents.append({"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nQuestion: {prompt}"}]})
            
            payload = {"contents": contents}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text']
                actions = cls._extract_actions(prompt, text)
                return {"text": text, "actions": actions, "provider": "gemini"}
        except Exception as e:
            print(f"Gemini API error, falling back: {e}")
            return None

    @classmethod
    def _call_openai(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None) -> dict:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if history and isinstance(history, list):
                for h in history[-6:]:
                    role = "user" if h.get("sender") == "user" else "assistant"
                    messages.append({"role": role, "content": h.get("text", "")})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
                "messages": messages,
                "temperature": 0.7
            }
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['choices'][0]['message']['content']
                actions = cls._extract_actions(prompt, text)
                return {"text": text, "actions": actions, "provider": "openai"}
        except Exception as e:
            print(f"OpenAI API error, falling back: {e}")
            return None

    @classmethod
    def _call_claude(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None) -> dict:
        try:
            url = "https://api.anthropic.com/v1/messages"
            msgs = []
            if history and isinstance(history, list):
                for h in history[-6:]:
                    role = "user" if h.get("sender") == "user" else "assistant"
                    msgs.append({"role": role, "content": h.get("text", "")})
            msgs.append({"role": "user", "content": prompt})

            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": msgs
            }
            headers = {
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['content'][0]['text']
                actions = cls._extract_actions(prompt, text)
                return {"text": text, "actions": actions, "provider": "claude"}
        except Exception as e:
            print(f"Claude API error, falling back: {e}")
            return None

    @classmethod
    def _call_fallback(cls, prompt: str, user_context: dict = None, history: list = None) -> dict:
        db_items = []
        try:
            from .models import AIKnowledgeBaseItem
            qs = AIKnowledgeBaseItem.objects.filter(is_active=True).values('category', 'question', 'answer', 'is_active')
            db_items = list(qs)
        except Exception as e:
            print(f"Failed to fetch DB knowledge items: {e}")

        from .knowledge_base import classify_intent_and_respond
        res = classify_intent_and_respond(prompt, user_context, history, db_items)
        res["provider"] = "knowledge_base"
        return res

    @staticmethod
    def _extract_actions(prompt: str, response_text: str) -> list:
        combined = (prompt + " " + response_text).lower()
        actions = []
        if any(k in combined for k in ['luggage', 'baggage', 'allowance', 'extra weight']):
            actions.append(QUICK_NAV_ACTIONS['luggage'])
        if any(k in combined for k in ['parcel', 'package', 'shipment', 'send']):
            actions.append(QUICK_NAV_ACTIONS['sender'])
        if any(k in combined for k in ['wallet', 'escrow', 'payment', 'payout', 'earn', 'income']):
            actions.append(QUICK_NAV_ACTIONS['wallet'])
        if any(k in combined for k in ['trust', 'kyc', 'verify', 'fraud', 'security']):
            actions.append(QUICK_NAV_ACTIONS['trust'])
        return actions
