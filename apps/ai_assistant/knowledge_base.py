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
    text_lower = text.lower()
    # Check Gujarati Unicode range or common Gujarati words/phrases (script + transliterated)
    gu_keywords = [
        'kem cho', 'su che', 'bhaadu', 'mokli', 'shakay', 'paisa', 'maate', 'bhai', 
        'karti nathi', 'nathi', 'aava', 'joiye', 'karo', 'work karti nathi', 'su', 
        'kayi rite', 'samaj', 'kaye', 'chhe', 'shuru', 'chalu', 'kem'
    ]
    if re.search(r'[\u0A80-\u0AFF]', text) or any(w in text_lower for w in gu_keywords):
        return 'gu'
    # Check Hindi/Devanagari range or common Hindi words
    hi_keywords = [
        'kya', 'kaise', 'kaise kaam', 'karna', 'bhej', 'sakta', 'bhejna', 'aushadhi', 
        'paise', 'kaise kamaye', 'nahi chal', 'kam nahi'
    ]
    if re.search(r'[\u0900-\u097F]', text) or any(w in text_lower for w in hi_keywords):
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
    # -----------------------------------------------------------------------
    # GUJARATI LANGUAGE INTENT RESPONSES
    # -----------------------------------------------------------------------
    if lang == 'gu':
        if any(k in query_lower for k in ['drug', 'narcotic', 'ganja', 'dawa', 'illegal', 'bandhi', 'aushadhi', 'medicine', 'dava', 'દવા', 'દવાઓ', 'ઔષધ', 'ડ્રગ્સ', 'પ્રતિબંધિત']):
            if any(k in query_lower for k in ['dawa', 'dava', 'medicine', 'aushadhi', 'doctor', 'prescription', 'દવા', 'દવાઓ', 'ઔષધ', 'ડોક્ટર', 'પ્રિસ્ક્રિપ્શન']):
                return {
                    "text": (
                        "💊 **દવાઓ (Medicines) મોકલવા અંગેના સત્તાવાર નિયમો & સુરક્ષા પોલિસી:**\n\n"
                        "FlyoraGo પ્લેટફોર્મ પર ફક્ત માન્ય અને સુરક્ષિત દવાઓ જ મોકલી શકાય છે:\n\n"
                        "૧. **ડોક્ટરનું વૈધ પ્રિસ્ક્રિપ્શન (Doctor Prescription)**: દવાના માલિકના નામ સાથે મેળ ખાતું ડોક્ટરનું ઓરિજિનલ લેટર કે પ્રિસ્ક્રિપ્શન બતાવવું ફરજિયાત છે.\n"
                        "૨. **ઓરિજિનલ સીલ્ડ પેકિંગ (Sealed Commercial Packaging)**: દવાઓ ઓરિજિનલ સીલ્ડ બોક્સ કે પેકિંગમાં જ હોવી જોઈએ. ખુલ્લી ગોળીઓ કે સ્ટ્રીપ્સ સ્વીકારવામાં આવતી નથી.\n"
                        "૩. **એરપોર્ટ હેન્ડઓવર તપાસ (Physical Inspection)**: ફ્લાઈટમાં જતા પહેલા ટ્રેવલર (Traveler) દવાના બોક્સ અને બિલની સ્થળ પર જ ચકાસણી કરે છે.\n"
                        "૪. **ગેરકાયદેસર ડ્રગ્સ પર સંપૂર્ણ પ્રતિબંધ (Zero-Tolerance)**: કોઈપણ પ્રકારના નશીલા પદાર્થો કે ગેરકાયદે કેમિકલ્સ પર ૧૦૦% પ્રતિબંધ છે."
                    ),
                    "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                    "timestamp": "Just now"
                }
            return {
                "text": (
                    "🚫 **પ્રતિબંધિત વસ્તુઓની નીતિ (Prohibited Items & Safety Policy):**\n\n"
                    "FlyoraGo પ્લેટફોર્મ પર કોઈપણ ગેરકાયદેસર કે જોખમી સામાન મોકલવો સખત ગુનો છે:\n\n"
                    "• **ડ્રગ્સ અને નશીલા પદાર્થો**: તમામ પ્રકારના ગેરકાયદેસર ડ્રગ્સ, ગાંજો કે સિન્થેટિક કેમિકલ્સ.\n"
                    "• **હથિયારો અને વિસ્ફોટકો**: બંદૂક, ચાકુ, દારૂગોળો, ફટાકડા કે ભયાનક કેમિકલ્સ.\n"
                    "• **ગેરકાયદેસર સામાન**: બિનઅધિકૃત ચલણ કે સરકાર દ્વારા પ્રતિબંધિત વસ્તુઓ.\n\n"
                    "**સુરક્ષા કાર્યવાહી:**\n"
                    "૧. ટ્રેવલર સામાન ચેક-ઈન કરતા પહેલા દરેક સામાનની ફિઝિકલ તપાસ કરે છે.\n"
                    "૨. નિયમનું ઉલ્લંઘન કરનારનું એકાઉન્ટ કાયમ માટે સસ્પેન્ડ કરી એવિએશન પોલીસને જાણ કરાશે."
                ),
                "actions": [QUICK_NAV_ACTIONS["trust"]],
                "timestamp": "Just now"
            }
        
        if any(k in query_lower for k in ['luggage', 'bhaadu', 'weight', 'kilo', 'baggage', 'samman', 'luggage sharing']):
            return {
                "text": (
                    "🧳 **લગેજ શેરિંગ (Luggage Sharing) ની કામગીરી અને નિયમો:**\n\n"
                    "FlyoraGo મુસાફરોની વધારાની લગેજ કેપેસિટી અને સામાન મોકલનાર યુઝર્સને કનેક્ટ કરે છે:\n\n"
                    "૧. **ફ્લાઈટ લિસ્ટિંગ**: ફ્લાઈટ મુસાફર પોતાનો ફ્લાઈટ રૂટ અને વધારાનું વજન (દા.ત. 15 kg) લિસ્ટ કરી કમાણી કરી શકે છે.\n"
                    "૨. **રિક્વેસ્ટ & બુકિંગ**: સામાન મોકલનાર યુઝર પોતાના રૂટની ફ્લાઈટ શોધી ઓર્ડર બુક કરે છે.\n"
                    "૩. **૧૦૦% એસ્ક્રો વોલેટ પેમેન્ટ**: પેમેન્ટ સુરક્ષિત રીતે FlyoraGo Escrow Vault માં જમા થાય છે, જે મુસાફરને અગાઉથી મળતું નથી.\n"
                    "૪. **૬-અંકનો OTP કન્ફર્મેશન**: સામાન પહોંચ્યા પછી રેસિપિએન્ટ OTP આપે એટલે તરત જ પેમેન્ટ ટ્રેવલરના વોલેટમાં જમા થઈ જાય છે."
                ),
                "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["trips"]],
                "timestamp": "Just now",
                "is_fallback": True
            }

        if any(k in query_lower for k in ['trust', 'stranger', 'paisa', 'payment', 'escrow', 'safe', 'wallet', 'refund', 'money']):
            return {
                "text": (
                    "🛡️ **સુરક્ષા, એસ્ક્રો પેમેન્ટ અને ટ્રસ્ટ આર્કિટેક્ચર (Trust & Security):**\n\n"
                    "FlyoraGo પ્લેટફોર્મ પર તમારો સામાન અને પૈસા ૧૦૦% સુરક્ષિત રહે છે:\n\n"
                    "૧. **ગવર્નમેન્ટ ID અને પાસપોર્ટ KYC**: તમામ યુઝર્સ અને મુસાફરોનું ગવર્નમેન્ટ પાસપોર્ટ વેરિફિકેશન થાય છે.\n"
                    "૨. **૧૦૦% એસ્ક્રો વોલેટ લોક**: તમારું પેમેન્ટ એસ્ક્રો વૉલ્ટમાં લોક રહે છે – મુસાફરને ડિલિવરી પહેલા પૈસા મળતા નથી.\n"
                    "૩. **૬-અંકનો ડિલિવરી OTP**: સામાન યોગ્ય વ્યક્તિ સુધી પહોંચે અને OTP દાખલ થાય ત્યારે જ પેમેન્ટ રિલીઝ થાય છે.\n"
                    "૪. **૧૦૦% રિફંડ ગેરંટી**: જો ફ્લાઈટ કેન્સલ થાય કે ટ્રેવલર સામાન ના પહોંચાડે, તો સુંદરને ૧૦૦% પૈસા પાછા મળે છે."
                ),
                "actions": [QUICK_NAV_ACTIONS["wallet"], QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["support"]],
                "timestamp": "Just now",
                "is_fallback": True
            }

        return {
            "text": (
                "✈️ **FlyoraGo પ્લેટફોર્મ સેવાઓ અને સુરક્ષા નીતિ (Platform Overview):**\n\n"
                "૧. **લગેજ શેરિંગ (Luggage Sharing)**: ફ્લાઈટ મુસાફરો પોતાની વધારાની ચેક-ઈન સ્પેસ શેર કરીને કમાણી કરી શકે છે.\n"
                "૨. **પાર્સલ ડિલિવરી (Parcel Delivery)**: સુંદર પોતાના પાર્સલ સીધા મેચિંગ ફ્લાઈટ ટ્રેવલર સાથે મોકલી શકે છે.\n"
                "૩. **એસ્ક્રો વોલેટ લોક (Escrow Protection)**: ૧૦૦% નાણાકીય સુરક્ષા – 6-Digit OTP પછી જ પેમેન્ટ રિલીઝ થાય છે.\n"
                "૪. **પાસપોર્ટ KYC વેરિફિકેશન**: ગવર્નમેન્ટ આઈડી ચેક દ્વારા ચોરી કે ફ્રોડ સામે રક્ષણ.\n\n"
                "તમારો પ્રશ્ન ગુજરાતી અથવા English માં મુક્તપણે પૂછો!"
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now",
            "is_fallback": True
        }

    # -----------------------------------------------------------------------
    # HINDI LANGUAGE INTENT RESPONSES
    # -----------------------------------------------------------------------
    if lang == 'hi':
        if any(k in query_lower for k in ['drug', 'narcotic', 'dawa', 'illegal', 'hathiyar', 'banned', 'medicine']):
            if any(k in query_lower for k in ['dawa', 'medicine', 'aushadhi', 'doctor']):
                return {
                    "text": (
                        "💊 **दवाइयां (Medicines) भेजने के सुरक्षा नियम:**\n\n"
                        "1. **डॉक्टर का पर्चा अनिवार्य**: केवल वैध और डॉक्टर द्वारा प्रमाणित दवाइयां ही भेजी जा सकती हैं।\n"
                        "2. **मूल सीलबंद पैकिंग**: दवाइयां कंपनी की मूल पैकेजिंग में होनी चाहिए।\n"
                        "3. **नशीले पदार्थों पर सख्त प्रतिबंध**: किसी भी प्रकार के अवैध ड्रग्स या खतरनाक केमिकल पर पूर्ण प्रतिबंध है।\n"
                        "4. **भौतिक जांच**: यात्री (Traveler) पैकेज स्वीकार करने से पहले बिल और दवा की जांच करता है।"
                    ),
                    "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                    "timestamp": "Just now",
                    "is_fallback": True
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
                "timestamp": "Just now",
                "is_fallback": True
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
            "timestamp": "Just now",
            "is_fallback": True
        }

    # -----------------------------------------------------------------------
    # ENGLISH INTENT RESPONSES (AUTHORITATIVE, STEP-BY-STEP & FACTUAL)
    # -----------------------------------------------------------------------
    # 1. INTENT: Prohibited Items vs Prescription Medicine Policy
    if any(k in query_lower for k in ['drug', 'drugs', 'narcotic', 'weed', 'weapon', 'gun', 'knife', 'explosive', 'illegal', 'contraband', 'banned', 'restricted', 'smuggle', 'medicine', 'dawa', 'pills', 'pharma']):
        if any(k in query_lower for k in ['medicine', 'prescription', 'dawa', 'pills', 'pharma', 'doctor', 'medical']):
            return {
                "text": (
                    "💊 **FlyoraGo Prescription Medicine Transport Policy:**\n\n"
                    "Over-the-counter and prescription medicines are permitted on FlyoraGo ONLY under strict, verified compliance rules:\n\n"
                    "**Mandatory Safety Requirements:**\n"
                    "1. **Valid Doctor Prescription**: A official licensed doctor's prescription matching the sender/owner's legal name must accompany the package.\n"
                    "2. **Original Sealed Commercial Packaging**: Medicines must remain factory-sealed in original commercial blisters/boxes with visible batch numbers and expiry dates. Loose pills or unsealed bottles are strictly rejected.\n"
                    "3. **Physical Inspection at Handover**: The traveler inspects the physical prescription and sealed packaging at airport handover prior to flight departure.\n"
                    "4. **Strict Narcotics & Controlled Substances Ban**: Narcotics, psychotropic substances, or unverified chemical compounds without government clearance are 100% prohibited."
                ),
                "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
                "timestamp": "Just now"
            }

        return {
            "text": (
                "🚫 **FlyoraGo Prohibited Items Policy & Zero-Tolerance Safety Rules:**\n\n"
                "FlyoraGo strictly prohibits the carriage, transport, or sharing of any illegal, hazardous, or restricted items:\n\n"
                "• **Drugs & Narcotics**: Illegal narcotics, synthetic substances, unverified chemical compounds, or marijuana.\n"
                "• **Weapons & Explosives**: Firearms, ammunition, knives, fireworks, flammable liquids, or dangerous goods.\n"
                "• **Restricted Contraband**: Undeclared currency exceeding legal customs thresholds, counterfeit goods, or illegal wildlife products.\n\n"
                "**Safety & Legal Enforcement:**\n"
                "1. **Mandatory Handover Inspection**: Travelers photograph and physically inspect all items before flight check-in.\n"
                "2. **Immediate Rejection**: Unverified or suspicious packages are rejected on the spot.\n"
                "3. **Law Enforcement Escalation**: Violations result in permanent account bans, escrow forfeiture, and immediate reporting to aviation police and law enforcement."
            ),
            "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"]],
            "timestamp": "Just now"
        }

    # 2. INTENT: Luggage Sharing & How FlyoraGo Works
    if any(k in query_lower for k in ['luggage sharing', 'how luggage sharing work', 'how flyorago work', 'how does flyorago work', 'what is flyorago', 'overview', 'about platform', 'how it works', 'process']):
        return {
            "text": (
                "✈️ **FlyoraGo International Luggage Sharing & Parcel Marketplace:**\n\n"
                "FlyoraGo connects verified international flight travelers who have unused check-in baggage capacity with senders who need packages delivered quickly and safely.\n\n"
                "**Complete Step-by-Step Execution:**\n"
                "1. **Publish Flight Route**: Traveler registers flight details, PNR, departure date, and available baggage weight (e.g. 10–30 KG).\n"
                "2. **Search & Book**: Sender searches matching verified flight routes and submits a package shipping request.\n"
                "3. **Traveler Inspection**: Traveler reviews package category, weight, and description, then accepts the booking.\n"
                "4. **100% Escrow Vault Lock**: Sender deposits the reward safely into the **FlyoraGo Escrow Vault**. Funds are NEVER paid upfront to the traveler.\n"
                "5. **Physical Airport Handover**: Traveler meets sender, performs physical photo inspection, and uploads verification photos.\n"
                "6. **Cryptographic 6-Digit OTP Delivery**: Recipient provides the secret **6-digit OTP** at delivery, instantly releasing payout to the traveler's wallet."
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 3. INTENT: Traveller Earning & Income Workflow
    if any(k in query_lower for k in ['earn', 'earning', 'income', 'make money', 'traveller income', 'reward price', 'payout timeline', 'how travellers earn']):
        return {
            "text": (
                "💰 **Traveller Earning & Payout Workflow:**\n\n"
                "Travelers monetize unused airline check-in baggage capacity by delivering verified parcels.\n\n"
                "**Earning Architecture:**\n"
                "• **Competitive Earnings**: Earn $10 – $30 per KG depending on flight route demand and urgency.\n"
                "• **100% Protected Escrow**: Sender payments are secured in Escrow before flight departure.\n"
                "• **Instant OTP Release**: Funds transfer immediately to your Flyora Wallet upon entering the recipient's valid **6-digit OTP** code at delivery."
            ),
            "actions": [QUICK_NAV_ACTIONS["trips"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 4. INTENT: Sender Delivery & Tracking Workflow
    if any(k in query_lower for k in ['send package', 'sender workflow', 'track delivery', 'shipping steps', 'package request', 'send parcel']):
        return {
            "text": (
                "📦 **Sender Package Shipping & Real-Time Tracking Workflow:**\n\n"
                "1. **Create Parcel Request**: Specify weight, dimensions, category, origin, and destination.\n"
                "2. **Match Verified Traveler**: Select from verified travelers flying your exact flight route.\n"
                "3. **Escrow Vault Deposit**: Deposit shipping reward safely into Escrow (never direct cash/wire transfers).\n"
                "4. **Airport Handover**: Meet traveler for physical item inspection and photo logging.\n"
                "5. **Real-Time Flight Tracking**: Monitor flight departure, transit, and arrival milestones.\n"
                "6. **Recipient OTP Confirmation**: Share the secret 6-digit OTP with your recipient to confirm physical delivery."
            ),
            "actions": [QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["trips"]],
            "timestamp": "Just now"
        }

    # 5. INTENT: TRUST_AND_SAFETY (Trust, Stranger Concerns, KYC, Verification, Fraud, Non-Delivery Protection)
    trust_safety_keywords = [
        'trust', 'stranger', 'genuine', 'real traveller', 'real traveler', 'how do i know',
        'steal', 'stolen', 'stole', 'rob', 'thief', 'lost', 'not deliver', 'does not deliver',
        'fails to deliver', 'fail to deliver', 'fraud', 'scam', 'cheat', 'fake', 'safe',
        'safety', 'kyc', 'verify', 'verification', 'passport', 'id verification',
        'protection', 'protect', 'secure', 'security', 'guarantee', 'reliable', 'reliability'
    ]
    if any(k in query_lower for k in trust_safety_keywords):
        return {
            "text": (
                "🛡️ **FlyoraGo Multi-Layer Trust, Safety & Fraud Protection Architecture:**\n\n"
                "FlyoraGo provides bulletproof security for senders and travelers through 5 integrated security layers:\n\n"
                "1. **Mandatory Passport & ID KYC**: Every traveler must submit government passport and national ID verification before accepting luggage requests.\n"
                "2. **100% Protected Escrow Vault**: Shipping rewards are locked securely in the Escrow Vault and are NEVER paid to travelers upfront.\n"
                "3. **6-Digit Cryptographic OTP Handover**: Funds are released ONLY when the recipient enters the secret 6-digit OTP code at physical delivery.\n"
                "4. **Transparent Member Ratings & Reviews**: Users can inspect verified past transaction history, ratings, and member trust scores.\n"
                "5. **Dispute Resolution & 100% Refund Guarantee**: If a traveler vanishes, delays delivery, or fails verification, click 'Raise Dispute' to lock funds instantly and receive a 100% full refund to your wallet while permanently banning the violator."
            ),
            "intent": "TRUST_AND_SAFETY",
            "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 6. INTENT: Payments, Escrow & Refund Rules
    if any(k in query_lower for k in ['payment', 'escrow', 'wallet', 'withdraw', 'refund', 'cancellation', 'money']):
        return {
            "text": (
                "💳 **FlyoraGo 100% Escrow Vault & Refund Guarantee:**\n\n"
                "• **100% Escrow Protection**: All payments are held in the secure FlyoraGo Escrow Vault upon booking.\n"
                "• **Instant Release**: Payout releases to the traveler wallet immediately upon recipient 6-digit OTP entry.\n"
                "• **100% Money-Back Refund**: Senders get a full refund if a trip is cancelled, delayed, or traveler fails physical verification."
            ),
            "actions": [QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # 7. INTENT: Disputes & Customer Support
    if any(k in query_lower for k in ['dispute', 'damage', 'missing', 'late', 'complaint', 'claim', 'support', 'help']):
        return {
            "text": (
                "⚠️ **Dispute Resolution & Customer Protection:**\n\n"
                "If a parcel is damaged, delayed, or unverified:\n"
                "1. **Raise Dispute**: Click 'Raise Dispute' in your booking dashboard before sharing the OTP code.\n"
                "2. **Freeze Escrow**: Funds are locked instantly in Escrow during investigation.\n"
                "3. **Admin Investigation**: Support team inspects handover photos, luggage weight receipts, and chat logs to issue a 100% refund."
            ),
            "actions": [QUICK_NAV_ACTIONS["support"]],
            "timestamp": "Just now"
        }

    # 8. STRUCTURED FALLBACK FOR AMBIGUOUS QUERIES
    if history and len(history) > 0:
        return {
            "text": (
                "I am here to help with FlyoraGo platform services! "
                "Could you please clarify your question regarding luggage sharing, parcel delivery, escrow payments, or safety rules?"
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"]],
            "timestamp": "Just now",
            "is_fallback": True
        }

    return {
        "text": (
            "I am Flyora AI, your expert platform assistant for FlyoraGo!\n\n"
            "Here is how I can assist you right now:\n\n"
            "1. **🧳 Luggage Sharing**: How travelers publish extra baggage capacity (10-30 KG) & earn.\n"
            "2. **📦 Parcel Delivery**: How senders book verified travelers on matching flight routes.\n"
            "3. **💰 Escrow Security & Wallet**: 100% funds protection releasing only via 6-digit recipient OTP.\n"
            "4. **🛡️ Passport KYC & Trust Score**: Anti-fraud verification for travelers & senders.\n"
            "5. **💊 Prescription Medicine Rules**: Doctor prescription required; zero tolerance for prohibited drugs.\n\n"
            "Please ask any question in English, Gujarati, or Hindi!"
        ),
        "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
        "timestamp": "Just now",
        "is_fallback": True
    }




def retrieve_knowledge_context(prompt_text: str, user_context: dict = None, db_items: list = None) -> str:
    """
    Retrieves comprehensive, structured knowledge context from live DB, custom admin FAQs,
    and official FlyoraGo policy definitions to feed into Google Gemini RAG reasoning.
    """
    context_blocks = []

    # 1. Query Live DB stats if applicable
    live_res = query_live_stats(prompt_text.lower(), user_context)
    if live_res and live_res.get('text'):
        context_blocks.append(f"--- LIVE PLATFORM / USER DATA ---\n{live_res['text']}")

    # 2. Custom Admin DB FAQs
    if db_items:
        admin_faqs = []
        for item in db_items:
            if item.get('is_active'):
                admin_faqs.append(f"Q: {item.get('question')}\nA: {item.get('answer')}")
        if admin_faqs:
            context_blocks.append("--- ADMIN MANAGED FAQS & KNOWLEDGE ITEMS ---\n" + "\n\n".join(admin_faqs))

    # 3. Core FlyoraGo Policies & Business Rules
    core_knowledge = """--- OFFICIAL FLYORAGO POLICIES & BUSINESS RULES ---

1. PROHIBITED ITEMS & SAFETY RULES:
- Prohibited: Illegal drugs, marijuana, narcotics, synthetic chemicals, firearms, weapons, ammunition, explosives, fireworks, counterfeit goods, undeclared currency over legal limits, illegal wildlife.
- Enforcement: Mandatory physical inspection of all items photo verified by traveler before flight departure. Immediate rejection of unverified packages. Permanent account ban + aviation police / law enforcement escalation for violations.

2. PRESCRIPTION MEDICINES POLICY:
- Over-the-counter & prescription medicines allowed ONLY with valid doctor's prescription matching patient/owner name.
- Medicines must be in original sealed commercial packaging.
- Traveler inspects prescription & sealed packaging prior to flight departure.
- Controlled substances or illegal drugs without government clearance are strictly banned.

3. HOW FLYORAGO WORKS & PLATFORM OVERVIEW:
- Connects verified international travelers with extra check-in baggage capacity with package senders.
- Traveler publishes flight route & available baggage weight (e.g. 10-30 KG).
- Sender searches matching routes & submits package request.
- Traveler inspects details & accepts.
- Sender deposits shipping payment safely into 100% Escrow Vault.
- Physical handover inspection + photo upload before check-in.
- Delivery confirmation via 6-digit cryptographic OTP code to release escrow payout to traveler wallet.

4. TRAVELLER EARNINGS & PAYOUTS:
- Travelers monetize unused check-in luggage weight.
- Rates: $10 - $30 per KG depending on flight route demand.
- 100% Escrow Vault hold protects funds before departure.
- Released instantly to Flyora Wallet upon valid 6-digit OTP delivery entry.

5. SENDER PACKAGE SHIPPING & TRACKING:
- Senders enter package weight, category, origin, and destination.
- Select verified traveler flying exact flight route.
- Deposit reward safely into Escrow Hold (never direct cash/wire transfer).
- Meet traveler for handover & physical inspection.
- Track real-time flight transit status.
- Share 6-digit OTP with recipient to complete delivery.

6. SAFETY, SECURITY, TRUST & STRANGER TRAVELLER CONCERNS (TRUST_AND_SAFETY):
- Why Trust Travelers: FlyoraGo builds trust through 5 security layers: Mandatory Government Passport/ID KYC, 100% Escrow Vault protection, Cryptographic 6-digit OTP delivery confirmation, Transparent Profiles with Ratings & Past History, and Dispute Resolution with 100% refund guarantee.
- Verification: Travellers are verified via government ID, passport, and flight ticket verification.
- Non-Delivery & Theft Prevention: If a traveler fails to deliver or attempts theft, funds remain 100% locked in Escrow Vault (never paid upfront). The recipient never provides the 6-digit OTP. Sender clicks 'Raise Dispute' to instantly freeze funds and receive a 100% full refund while violator is permanently banned and reported to aviation police / law enforcement.
- Fraud Prevention: Zero direct payments outside platform. Senders deposit into Escrow Vault. 6-digit cryptographic OTP is required for payout release.

7. PAYMENTS, ESCROW & REFUND POLICY:
- Escrow Vault locks funds upon booking acceptance.
- Funds released to traveler wallet upon valid 6-digit OTP code entry.
- 100% Full Refund to sender if trip is cancelled or traveler fails verification/inspection.

8. DISPUTES & CUSTOMER SUPPORT:
- Raise dispute immediately if package is damaged, delayed, or unverified BEFORE sharing OTP code.
- Escrow Vault is locked immediately during investigation.
- Admin support team reviews handover photos, baggage weight receipts, and chat logs."""


    context_blocks.append(core_knowledge)
    return "\n\n".join(context_blocks)

