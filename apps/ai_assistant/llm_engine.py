"""
Configurable LLM Provider Abstraction & RAG Reasoning Engine for Flyora AI
Integrates Google Gemini API as the primary reasoning engine while ensuring strict grounding
in FlyoraGo knowledge, policies, DB statistics, and admin FAQs.
"""

import os
import json
import hashlib
import urllib.request
import urllib.error
from django.conf import settings
from django.core.cache import cache
from .knowledge_base import (
    classify_intent_and_respond,
    retrieve_knowledge_context,
    QUICK_NAV_ACTIONS
)

GROUNDED_SYSTEM_PROMPT = """You are Flyora AI, the principal AI assistant and logistics intelligence engine for FlyoraGo — a peer-to-peer international travel luggage sharing and parcel delivery marketplace.

CRITICAL OPERATIONAL RULES:
1. STRICT KNOWLEDGE GROUNDING:
   - You MUST answer questions using ONLY the official FlyoraGo Knowledge Context provided below.
   - Do NOT use outside knowledge, unverified assumptions, or external facts not present in FlyoraGo context.
   - If the user asks something outside FlyoraGo platform services or policies, state honestly and clearly:
     "I do not have that specific information in FlyoraGo guidelines. I can only assist with questions regarding FlyoraGo luggage sharing, parcel shipping, safety policies, escrow payments, and account rules."

2. REASONING & RESPONSE EXCELLENCE (ChatGPT Style):
   - Answer directly first.
   - Explain HOW, WHY, WHAT IF, or COMPARE options logically when asked analytical, safety, or procedure questions.
   - Address topics like Trust, Fraud, Escrow, Delivery, Security, Wallet, and KYC with thorough step-by-step reasoning.
   - Use clear markdown formatting (bold headers, bullet points, numbered steps).
   - Maintain a crisp, professional, authoritative, and helpful tone.

3. STRICT POLICY PRESERVATION:
   - Trust & Safety / Stranger Concerns: Explain FlyoraGo's multi-layered security architecture: (1) Mandatory Passport & Government ID KYC verification, (2) 100% Escrow Vault protection (funds are never paid upfront), (3) 6-digit cryptographic OTP confirmation required from recipient, (4) Transparent member profiles, ratings, and transaction history, and (5) Dispute resolution with instant escrow fund lock & 100% refund protection.
   - Dangerous Goods & Prohibited Items: State zero tolerance, mandatory physical photo inspection prior to flight departure, immediate rejection of unverified items, permanent account ban, and law enforcement / aviation police escalation.
   - Prescription Medicines: Must explain doctor's prescription requirement matching owner name + original sealed commercial packaging + physical traveler inspection before flight departure. Unverified drugs or narcotics strictly banned.
   - Payments & Escrow: Explain 100% Escrow Vault hold, zero direct outside cash/wire transfers, and instant payout release to wallet upon 6-digit cryptographic OTP code entry at destination.
   - Safety & KYC: Passport/National ID verification mandatory for all travelers & senders.

4. MULTI-LANGUAGE SUPPORT:
   - Detect the language of the user question (English, Gujarati, Hindi, etc.) and respond in that exact language.


--- FLYORAGO OFFICIAL KNOWLEDGE CONTEXT ---
{context}
"""


class LLMEngine:
    @staticmethod
    def get_provider() -> str:
        return getattr(settings, 'AI_PROVIDER', os.getenv('AI_PROVIDER', 'gemini')).lower()

    @classmethod
    def generate_response(cls, prompt_text: str, user_context: dict = None, history: list = None) -> dict:
        provider = cls.get_provider()
        
        # Check in-memory cache for identical prompt & recent history
        cache_key = cls._build_cache_key(prompt_text, user_context, history)
        cached_res = cache.get(cache_key)
        if cached_res:
            return cached_res

        # Fetch active Admin DB FAQs
        db_items = cls._get_active_db_faqs()

        # -------------------------------------------------------------------
        # TIER 1: Existing Deterministic Knowledge Base / Intent Engine
        # -------------------------------------------------------------------
        # If the query matches an explicit, existing policy or DB query
        # (e.g. Prescription Medicines, Prohibited Items/Drugs, Live DB Stats, Admin FAQs),
        # return the EXACT existing answer directly without altering or invoking Gemini.
        kb_res = classify_intent_and_respond(prompt_text, user_context, history, db_items)
        if kb_res and not kb_res.get('is_fallback', False):
            kb_res["provider"] = "knowledge_base"
            cache.set(cache_key, kb_res, timeout=300)
            return kb_res

        # -------------------------------------------------------------------
        # TIER 2: Gemini RAG Intelligence Layer
        # -------------------------------------------------------------------
        # For unknown questions, new scenarios, what-if questions, trust/fraud
        # concerns, comparison questions, or complex multi-feature reasoning.
        res = None

        # 1. Try Google Gemini API
        if provider == 'gemini':
            api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
            if api_key:
                res = cls._call_gemini(prompt_text, api_key, user_context, history, db_items)

        # 2. Try OpenAI API
        elif provider == 'openai':
            api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            if api_key:
                res = cls._call_openai(prompt_text, api_key, user_context, history, db_items)

        # 3. Try Anthropic Claude API
        elif provider == 'claude':
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY', ''))
            if api_key:
                res = cls._call_claude(prompt_text, api_key, user_context, history, db_items)

        # 4. Fallback to Tier 1 response if provider fails or is unconfigured
        if not res:
            res = kb_res if kb_res else cls._call_fallback(prompt_text, user_context, history, db_items)

        # Store successful result in cache (TTL 300s = 5 mins)
        if res and res.get('text'):
            cache.set(cache_key, res, timeout=300)

        return res


    @classmethod
    def _call_gemini(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
        models = [
            getattr(settings, 'GEMINI_MODEL', 'gemini-flash-latest'),
            'gemini-flash-latest',
            'gemini-flash-lite-latest',
            'gemini-2.0-flash',
            'gemini-1.5-flash'
        ]
        # Preserve order while deduplicating
        candidate_models = list(dict.fromkeys([m for m in models if m]))

        try:
            # Retrieve RAG context from knowledge base & live DB stats
            context_str = retrieve_knowledge_context(prompt, user_context, db_items)
            system_instruction = GROUNDED_SYSTEM_PROMPT.format(context=context_str)

            contents = []

            # Conversation Memory: Include up to last 10 messages from history
            if history and isinstance(history, list):
                for h in history[-10:]:
                    sender_role = "user" if h.get("sender") == "user" else "model"
                    msg_text = h.get("text", "").strip()
                    if msg_text:
                        contents.append({
                            "role": sender_role,
                            "parts": [{"text": msg_text}]
                        })

            # Append current turn with grounded system instructions & context
            current_prompt_payload = f"{system_instruction}\n\nUSER QUESTION: {prompt}"
            contents.append({
                "role": "user",
                "parts": [{"text": current_prompt_payload}]
            })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.3,  # Low temperature for precise grounded factual reasoning
                    "maxOutputTokens": 1024
                }
            }

            for model in candidate_models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with urllib.request.urlopen(req, timeout=12) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        candidates = result.get('candidates', [])
                        if candidates and candidates[0].get('content', {}).get('parts'):
                            text = candidates[0]['content']['parts'][0]['text'].strip()
                            actions = cls._extract_actions(prompt, text)
                            return {
                                "text": text,
                                "actions": actions,
                                "provider": "gemini",
                                "timestamp": "Just now"
                            }
                except urllib.error.HTTPError as he:
                    print(f"Gemini API model '{model}' HTTP Error {he.code}. Trying next model...")
                    continue
                except Exception as e:
                    print(f"Gemini API model '{model}' note: {type(e).__name__} occurred.")
                    continue

            return None

        except Exception as e:
            # Security: NEVER log or expose Gemini API key in error logs
            print(f"Gemini API execution note: {type(e).__name__} occurred, engaging knowledge fallback.")
            return None

    @classmethod
    def _call_openai(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            context_str = retrieve_knowledge_context(prompt, user_context, db_items)
            system_instruction = GROUNDED_SYSTEM_PROMPT.format(context=context_str)

            messages = [{"role": "system", "content": system_instruction}]
            if history and isinstance(history, list):
                for h in history[-8:]:
                    role = "user" if h.get("sender") == "user" else "assistant"
                    messages.append({"role": role, "content": h.get("text", "")})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
                "messages": messages,
                "temperature": 0.3
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
                return {"text": text, "actions": actions, "provider": "openai", "timestamp": "Just now"}
        except Exception as e:
            print(f"OpenAI API note: {type(e).__name__} occurred, engaging knowledge fallback.")
            return None

    @classmethod
    def _call_claude(cls, prompt: str, api_key: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
        try:
            url = "https://api.anthropic.com/v1/messages"
            context_str = retrieve_knowledge_context(prompt, user_context, db_items)
            system_instruction = GROUNDED_SYSTEM_PROMPT.format(context=context_str)

            msgs = []
            if history and isinstance(history, list):
                for h in history[-8:]:
                    role = "user" if h.get("sender") == "user" else "assistant"
                    msgs.append({"role": role, "content": h.get("text", "")})
            msgs.append({"role": "user", "content": prompt})

            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "system": system_instruction,
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
                return {"text": text, "actions": actions, "provider": "claude", "timestamp": "Just now"}
        except Exception as e:
            print(f"Claude API note: {type(e).__name__} occurred, engaging knowledge fallback.")
            return None

    @classmethod
    def _call_fallback(cls, prompt: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
        if db_items is None:
            db_items = cls._get_active_db_faqs()

        res = classify_intent_and_respond(prompt, user_context, history, db_items)
        
        # Step 8: Never show welcome menu after the first message when conversation history exists
        if history and len(history) > 0:
            if "How can I assist you today?" in res.get("text", ""):
                res["text"] = (
                    "I am here to help with FlyoraGo platform services! "
                    "Could you please clarify your question regarding luggage sharing, parcel delivery, escrow payments, or safety rules?"
                )

        res["provider"] = "knowledge_base"
        return res

    @staticmethod
    def _get_active_db_faqs() -> list:
        try:
            from .models import AIKnowledgeBaseItem
            qs = AIKnowledgeBaseItem.objects.filter(is_active=True).values('category', 'question', 'answer', 'is_active')
            return list(qs)
        except Exception as e:
            print(f"Failed to fetch DB knowledge items: {e}")
            return []

    @staticmethod
    def _build_cache_key(prompt: str, user_context: dict = None, history: list = None) -> str:
        recent_hist = ""
        if history and isinstance(history, list):
            recent_hist = "|".join([f"{h.get('sender')}:{h.get('text')}" for h in history[-2:]])
        raw_str = f"{prompt.strip().lower()}:{user_context.get('id', '') if user_context else ''}:{recent_hist}"
        return f"flyora_ai_cache:{hashlib.md5(raw_str.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _extract_actions(prompt: str, response_text: str) -> list:
        combined = (prompt + " " + response_text).lower()
        actions = []
        if any(k in combined for k in ['luggage', 'baggage', 'allowance', 'extra weight', 'check-in']):
            actions.append(QUICK_NAV_ACTIONS['luggage'])
        if any(k in combined for k in ['parcel', 'package', 'shipment', 'send']):
            actions.append(QUICK_NAV_ACTIONS['sender'])
        if any(k in combined for k in ['wallet', 'escrow', 'payment', 'payout', 'earn', 'income', 'refund']):
            actions.append(QUICK_NAV_ACTIONS['wallet'])
        if any(k in combined for k in ['trust', 'kyc', 'verify', 'fraud', 'security', 'passport']):
            actions.append(QUICK_NAV_ACTIONS['trust'])
        return actions
