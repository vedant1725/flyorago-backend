"""
Flyora AI Enterprise Knowledge Engine & Intent Classifier
Provides comprehensive project context, live DB stats querying, multi-language detection (English, Gujarati, Hindi),
prescription vs prohibited items policy, escrow rules, and customer support reasoning.
"""

import re
from django.contrib.auth import get_user_model

QUICK_NAV_ACTIONS = {
    "luggage": {"label": "Go to Luggage Sharing 🧳", "path": "/luggage-sharing"},
    "wallet": {"label": "Open My Wallet 💰", "path": "/wallet"},
    "sender": {"label": "Send a Package 📦", "path": "/sender"},
    "trips": {"label": "Publish a Flight Trip ✈️", "path": "/trips"},
    "trust": {"label": "Check Trust Score ⭐", "path": "/trust"},
    "kyc": {"label": "Verify Identity / KYC 🛡️", "path": "/kyc"},
    "support": {"label": "Customer Support 💬", "path": "/support"}
}


def detect_language(text: str) -> str:
    """Detects if query is in Gujarati, Hindi, or English."""
    # Check Gujarati Unicode range or common phonetic words
    if re.search(r'[\u0A80-\u0AFF]', text) or any(w in text.lower() for w in ['kem cho', 'su che', 'bhaadu', 'mokli', 'shakay', 'paisa', 'maate', 'bhai']):
        return 'gu'
    # Check Hindi/Devanagari range or common Hindi words
    if re.search(r'[\u0900-\u097F]', text) or any(w in text.lower() for w in ['kya', 'kaise', 'kaise kaam', 'karna', 'bhej', 'sakta', 'bhejna', 'aushadhi', 'paise', 'kaise kamaye']):
        return 'hi'
    return 'en'


def query_live_stats(query: str, user_context: dict = None) -> dict:
    """Queries live Django database statistics for user queries."""
    query_lower = query.lower()
    
    # 1. Live Active Travelers / Trips count query
    if any(k in query_lower for k in ['active traveller', 'active traveler', 'how many traveller', 'how many traveler', 'how many trips', 'active trips', 'total trips']):
        try:
            from trips.models import Trip
            User = get_user_model()
            active_trips_count = Trip.objects.filter(status='Active').count()
            if active_trips_count == 0:
                active_trips_count = Trip.objects.count()
            total_users = User.objects.count()
            return {
                "is_live_data": True,
                "text": (
                    f"📊 **Live FlyoraGo Platform Stats:**\n\n"
                    f"• **Active Registered Trips**: {active_trips_count} verified flight routes available for booking.\n"
                    f"• **Platform Members**: {total_users} verified travelers & senders.\n\n"
                    f"You can search matching travelers flying your route right away!"
                ),
                "actions": [QUICK_NAV_ACTIONS["trips"], QUICK_NAV_ACTIONS["sender"]]
            }
        except Exception as e:
            print(f"Error querying live stats: {e}")

    # 2. Live Wallet / Payout query
    if user_context and user_context.get('id') and any(k in query_lower for k in ['my wallet', 'my balance', 'wallet balance', 'pending payout', 'how much money']):
        try:
            from wallet.models import Wallet
            wallet_obj = Wallet.objects.filter(user_id=user_context['id']).first()
            balance = getattr(wallet_obj, 'balance', '0.00') if wallet_obj else '0.00'
            pending = getattr(wallet_obj, 'pending_balance', '0.00') if wallet_obj else '0.00'
            return {
                "is_live_data": True,
                "text": (
                    f"💰 **Your Live Wallet Status ({user_context.get('first_name', 'User')}):**\n\n"
                    f"• **Available Balance**: ₹{balance} / ${balance}\n"
                    f"• **Pending Escrow Payouts**: ₹{pending} / ${pending}\n\n"
                    f"Pending funds are released to your available balance immediately upon successful 6-digit OTP delivery confirmation."
                ),
                "actions": [QUICK_NAV_ACTIONS["wallet"]]
            }
        except Exception as e:
            print(f"Error querying wallet: {e}")

    # 3. Live Pending Requests query
    if user_context and user_context.get('id') and any(k in query_lower for k in ['my pending requests', 'my bookings', 'my package status', 'where is my package']):
        try:
            from bookings.models import Booking
            uid = user_context['id']
            my_bookings = Booking.objects.filter(sender_id=uid).order_by('-id')[:3]
            if my_bookings.exists():
                items_str = "\n".join([f"• **Booking #{b.id}**: {getattr(b, 'package_name', 'Package')} — Status: `{getattr(b, 'status', 'REQUEST_SENT')}`" for b in my_bookings])
                return {
                    "is_live_data": True,
                    "text": (
                        f"📦 **Your Recent Package Deliveries ({user_context.get('first_name', 'User')}):**\n\n"
                        f"{items_str}\n\n"
                        f"All package rewards remain 100% secured in FlyoraGo Escrow until final OTP delivery confirmation."
                    ),
                    "actions": [QUICK_NAV_ACTIONS["sender"]]
                }
        except Exception as e:
            print(f"Error querying bookings: {e}")

    return None


def classify_intent_and_respond(prompt_text: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
    """
    Analyzes intent, handles multi-language support (English, Gujarati, Hindi), live database queries,
    and returns authoritative, structured customer support responses.
    """
    query = prompt_text.strip()
    query_lower = query.lower()
    lang = detect_language(query)

    # Check live DB queries first
    live_res = query_live_stats(query_lower, user_context)
    if live_res:
        return {
            "text": live_res["text"],
            "actions": live_res["actions"],
            "timestamp": "Just now"
        }

    # Check Admin Custom DB Knowledge Base Items
    if db_items:
        for item in db_items:
            if item.get('is_active') and item.get('question', '').lower() in query_lower:
                return {
                    "text": item.get('answer'),
                    "actions": [QUICK_NAV_ACTIONS["support"]],
                    "timestamp": "Just now"
                }

    # -----------------------------------------------------------------------
    # GUJARATI LANGUAGE INTENT RESPONSES
    # -----------------------------------------------------------------------
    if lang == 'gu':
        if any(k in query_lower for k in ['drug', 'narcotic', 'ganja', 'dawa', 'illegal', 'bandhi', 'aushadhi']):
            if 'dawa' in query_lower or 'medicine' in query_lower:
                return {
                    "text": (
                        "💊 **દવાઓ (Medicines) મોકલવા અંગેના નિયમો:**\n\n"
                        "૧. **ડોક્ટરનું પ્રિસ્ક્રિપ્શન ફરજિયાત**: ફક્ત લીગલ/ડોક્ટર દ્વારા પ્રમાણિત દવાઓ જ મોકલી શકાય છે.\n"
                        "૨. **ગેરકાયદેસર ડ્રગ્સ પર સંપૂર્ણ પ્રતિબંધ**: કોઈપણ નશીલા પદાર્થો, ગેરકાયદે ડ્રગ્સ કે કેમિકલ્સ મોકલવા પર સખત પ્રતિબંધ છે.\n"
                        "૩. **તપાસ & ફોટો**: પેકેજ સ્વીકારતા પહેલા મુસાફર (Traveler) દવાના બોક્સ અને બિલની ચકાસણી કરે છે."
                    ),
                    "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                    "timestamp": "Just now"
                }
            return {
                "text": (
                    "🚫 **પ્રતિબંધિત વસ્તુઓની નીતિ (Prohibited Items Policy):**\n\n"
                    "FlyoraGo પર ગેરકાયદેસર કે જોખમી વસ્તુઓ મોકલવા પર સખત પ્રતિબંધ છે:\n"
                    "• **ડ્રગ્સ અને નશીલા પદાર્થો**: કોઈપણ પ્રકારના નશા કે ગેરકાયદે પદાર્થો.\n"
                    "• **હથિયારો અને વિસ્ફોટકો**: બંદૂક, ચાકુ, ફટાકડા કે ભયાનક કેમિકલ્સ.\n\n"
                    "**નિયમ ઉલ્લંઘન પર કાર્યવાહી:**\n"
                    "ખાતું કાયમ માટે બંધ કરવામાં આવશે અને એવિએશન પોલીસને જાણ કરવામાં આવશે."
                ),
                "actions": [QUICK_NAV_ACTIONS["trust"]],
                "timestamp": "Just now"
            }
        
        return {
            "text": (
                "✈️ **FlyoraGo કેવી રીતે કામ કરે છે (How It Works):**\n\n"
                "૧. **મુસાફર (Traveler)**: પોતાની ફ્લાઈટ અને ખાલી લગેજ કેપેસિટી (દા.ત. 15 kg) એડ કરે છે.\n"
                "૨. **મોકલનાર (Sender)**: પોતાની સુટકેસ/સામાન મોકલવા માટે ટ્રેવલર સર્ચ કરે છે.\n"
                "૩. **એસ્ક્રો પેમેન્ટ (Escrow Vault)**: પેમેન્ટ FlyoraGo એસ્ક્રો વોલેટમાં સુરક્ષિત રહે છે.\n"
                "૪. **OTP ડિલિવરી**: સામાન પહોંચ્યા પછી 6-અંકનો OTP આપવાથી પેમેન્ટ મુસાફરને મળે છે."
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"]],
            "timestamp": "Just now"
        }

    # -----------------------------------------------------------------------
    # HINDI LANGUAGE INTENT RESPONSES
    # -----------------------------------------------------------------------
    if lang == 'hi':
        if any(k in query_lower for k in ['drug', 'narcotic', 'dawa', 'illegal', 'hathiyar', 'banned']):
            if 'dawa' in query_lower or 'medicine' in query_lower:
                return {
                    "text": (
                        "💊 **दवाइयां (Medicines) भेजने के सुरक्षा नियम:**\n\n"
                        "1. **डॉक्टर का पर्चा अनिवार्य**: केवल वैध और डॉक्टर द्वारा प्रमाणित दवाइयां ही भेजी जा सकती हैं।\n"
                        "2. **नशीले पदार्थों पर सख्त प्रतिबंध**: किसी भी प्रकार के अवैध ड्रग्स या खतरनाक केमिकल पर पूर्ण प्रतिबंध है।\n"
                        "3. **भौतिक जांच**: यात्री (Traveler) पैकेज स्वीकार करने से पहले बिल और दवा की जांच करता है।"
                    ),
                    "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                    "timestamp": "Just now"
                }
            return {
                "text": (
                    "🚫 **प्रतिबंधित वस्तुओं की नीति (Prohibited Items Policy):**\n\n"
                    "FlyoraGo पर निम्नलिखित अवैध या खतरनाक वस्तुओं को ले जाना सख्त मना है:\n"
                    "• **ड्रग्स एवं नशीले पदार्थ**: अवैध दवाइयां या नियंत्रित नशीले पदार्थ।\n"
                    "• **हथियार एवं विस्फोटक**: हथियार, पटाखे या खतरनाक केमिकल।\n\n"
                    "**कार्रवाई**: नियम तोड़ने पर अकाउंट हमेशा के लिए सस्पेंड कर पुलिस को रिपोर्ट किया जाएगा।"
                ),
                "actions": [QUICK_NAV_ACTIONS["trust"]],
                "timestamp": "Just now"
            }

        return {
            "text": (
                "✈️ **FlyoraGo कैसे काम करता है (How It Works):**\n\n"
                "1. **यात्री (Traveler)**: अपनी फ्लाइट और उपलब्ध लगेज क्षमता (जैसे 15 KG) दर्ज करता है।\n"
                "2. **सेंडर (Sender)**: पैकेज भेजने के लिए मैचिंग यात्री खोजता है।\n"
                "3. **सुरक्षित एस्क्रो भुगतान**: पेमेंट FlyoraGo Escrow में सुरक्षित रहता है।\n"
                "4. **OTP डिलीवरी**: डिलीवरी पूरा होने पर 6-अंकों का OTP दर्ज करते ही यात्री को भुगतान मिल जाता है।"
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"]],
            "timestamp": "Just now"
        }

    # -----------------------------------------------------------------------
    # ENGLISH INTENT RESPONSES (AUTHORITATIVE & FACTUAL)
    # -----------------------------------------------------------------------
    actions = []

    # 1. INTENT: Prohibited Items vs Prescription Medicine Policy
    if any(k in query_lower for k in ['drug', 'drugs', 'narcotic', 'weed', 'weapon', 'gun', 'knife', 'explosive', 'illegal', 'contraband', 'banned', 'restricted', 'smuggle', 'medicine', 'dawa', 'pills']):
        if any(k in query_lower for k in ['medicine', 'prescription', 'dawa', 'pills', 'pharma', 'doctor']):
            return {
                "text": (
                    "💊 **Prescription Medicine Transport Policy:**\n\n"
                    "Over-the-counter and prescription medicines are allowed only under strict safety rules:\n\n"
                    "**Requirements:**\n"
                    "1. **Valid Doctor Prescription**: Must accompany the package with owner name matching documents.\n"
                    "2. **Original Sealed Packaging**: Medicines must be in sealed commercial packaging.\n"
                    "3. **Physical Inspection**: Traveler inspects prescription and packaging prior to flight acceptance.\n"
                    "4. **No Illegal Narcotics**: Controlled substances or illegal drugs without government clearance are strictly banned."
                ),
                "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                "timestamp": "Just now"
            }

        return {
            "text": (
                "🚫 **Prohibited Items Policy & Zero-Tolerance Safety Rules:**\n\n"
                "FlyoraGo strictly prohibits the transport or sharing of any illegal or dangerous goods:\n\n"
                "• **Drugs & Narcotics**: Illegal substances, synthetic drugs, or unverified chemicals.\n"
                "• **Weapons & Explosives**: Firearms, ammunition, knives, fireworks, or hazardous materials.\n"
                "• **Restricted Contraband**: Undeclared currency over legal limits, counterfeit items, or illegal wildlife.\n\n"
                "**Safety Enforcement:**\n"
                "1. **Mandatory Physical Inspection**: Travelers photograph and inspect all items before flight departure.\n"
                "2. **Immediate Rejection**: Any unverified package is rejected immediately.\n"
                "3. **Law Enforcement Escalation**: Violators face permanent account bans and aviation police reporting."
            ),
            "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
            "timestamp": "Just now"
        }

    # 2. INTENT: How FlyoraGo Works (Platform Overview)
    if any(k in query_lower for k in ['how it works', 'how does it work', 'what is flyorago', 'overview', 'about platform', 'process']):
        return {
            "text": (
                "✈️ **How FlyoraGo Works:**\n\n"
                "FlyoraGo connects verified international travelers who have extra luggage capacity with senders who need packages delivered securely.\n\n"
                "**Step-by-Step Process:**\n"
                "1. **Publish Flight Trip**: Traveler adds flight route, departure date, and available baggage space (e.g. 15 KG).\n"
                "2. **Find & Request**: Sender searches matching flight routes and submits a package request.\n"
                "3. **Traveler Acceptance**: Traveler inspects package details and accepts the request.\n"
                "4. **Escrow Hold**: Sender deposits shipping payment safely into **FlyoraGo Escrow Vault**.\n"
                "5. **Physical Pickup**: Traveler inspects physical items at handover and uploads photo verification.\n"
                "6. **OTP Delivery Confirmation**: Recipient provides the **6-Digit OTP code** to instantly release payment to the traveler."
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"]],
            "timestamp": "Just now"
        }

    # 3. INTENT: Traveller Earning & Income Workflow
    if any(k in query_lower for k in ['earn', 'earning', 'income', 'make money', 'traveller income', 'reward price', 'payout timeline', 'how travellers earn']):
        return {
            "text": (
                "💰 **Traveller Earning & Payout Workflow:**\n\n"
                "Travelers monetize unused airline check-in baggage capacity by delivering verified parcels.\n\n"
                "**Earning Rules:**\n"
                "• **Custom Reward Rates**: Earn per KG based on flight route popularity ($10 - $30 per KG).\n"
                "• **100% Escrow Hold**: Sender funds are locked in Escrow before flight departure.\n"
                "• **Instant Release**: Released directly to your Flyora Wallet upon valid 6-Digit OTP code entry at destination handover."
            ),
            "actions": [QUICK_NAV_ACTIONS["trips"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 4. INTENT: Sender Delivery & Tracking Workflow
    if any(k in query_lower for k in ['send package', 'sender workflow', 'track delivery', 'shipping steps', 'package request', 'send parcel']):
        return {
            "text": (
                "📦 **Sender Package Delivery Workflow:**\n\n"
                "1. **Create Request**: Enter parcel weight, category, origin, and destination.\n"
                "2. **Select Traveler**: Choose from verified travelers flying your exact route.\n"
                "3. **Escrow Payment**: Deposit reward safely into Escrow Hold.\n"
                "4. **Handover Inspection**: Meet traveler for physical inspection & photo verification.\n"
                "5. **Track Flight**: Track transit status updates in real-time.\n"
                "6. **Confirm Delivery**: Share the **6-Digit OTP** with the recipient to complete delivery."
            ),
            "actions": [QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["trips"]],
            "timestamp": "Just now"
        }

    # 5. INTENT: Safety, Security, KYC & Identity Protection
    if any(k in query_lower for k in ['security', 'safety', 'kyc', 'fraud', 'verify', 'passport', 'id verification', 'scam', 'protection']):
        return {
            "text": (
                "🛡️ **Safety, Security & Anti-Fraud Protection:**\n\n"
                "• **Mandatory Passport & National ID KYC**: Government ID verified profiles.\n"
                "• **Physical Inspection**: Required photo inspection prior to flight check-in.\n"
                "• **100% Escrow Vault**: Senders never pay travelers directly; funds remain in Escrow.\n"
                "• **Cryptographic OTP Handover**: 6-digit OTP verification prevents false claims."
            ),
            "actions": [QUICK_NAV_ACTIONS["kyc"], QUICK_NAV_ACTIONS["trust"]],
            "timestamp": "Just now"
        }

    # 6. INTENT: Payments, Escrow & Refund Rules
    if any(k in query_lower for k in ['payment', 'escrow', 'wallet', 'withdraw', 'refund', 'cancellation', 'money']):
        return {
            "text": (
                "💳 **Payment & Escrow Protection:**\n\n"
                "• **Escrow Vault**: Holds funds securely upon booking acceptance.\n"
                "• **Instant Release**: Released to traveler wallet upon valid 6-Digit OTP entry.\n"
                "• **100% Refund**: Senders get a full refund if a trip is cancelled or traveler fails verification."
            ),
            "actions": [QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 7. INTENT: Disputes & Customer Support
    if any(k in query_lower for k in ['dispute', 'damage', 'missing', 'late', 'complaint', 'claim', 'support', 'help']):
        return {
            "text": (
                "⚠️ **Dispute Resolution & Customer Support:**\n\n"
                "If a parcel is damaged, delayed, or unverified:\n"
                "1. **Raise Dispute**: Click 'Raise Dispute' before sharing the OTP code.\n"
                "2. **Freeze Escrow**: Funds are locked immediately during investigation.\n"
                "3. **Admin Review**: Support team inspects handover photos, weight receipts, and chat logs."
            ),
            "actions": [QUICK_NAV_ACTIONS["support"]],
            "timestamp": "Just now"
        }

    # 8. STRUCTURED FALLBACK FOR AMBIGUOUS QUERIES
    return {
        "text": (
            "I am Flyora AI, your FlyoraGo platform expert assistant. How can I assist you today?\n\n"
            "1. **How Luggage Sharing Works** (Connect with verified travelers)\n"
            "2. **Traveller Earning Process** (Monetize unused baggage capacity)\n"
            "3. **Package Safety & Prohibited Items** (Drugs, weapons & safety rules)\n"
            "4. **Payment, Escrow & Wallet** (100% protected escrow holds)\n\n"
            "Please ask any specific question in English, Gujarati, or Hindi!"
        ),
        "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"]],
        "timestamp": "Just now"
    }
