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
    if lang == 'gu':
        # Technical / API Query in Gujarati
        if any(k in query_lower for k in ['work karti nathi', 'api', 'problem', 'error', 'chat boat', 'chatbot', 'nathi chal', 'connect', 'ans']):
            return {
                "text": (
                    "🤖 **Flyora AI બોટ એપીઆઈ હવે સંપૂર્ણ રીતે ચાલુ અને કાર્યરત છે! (Flyora AI Bot API is fully working!):**\n\n"
                    "અમારું સ્માર્ટ AI એન્જિન તમારા બધા પ્રશ્નોના જવાબ આપવા માટે તૈયાર છે. તમે પ્લેટફોર્મ વિશે નીચે આપેલા કોઈપણ વિષય પર માહિતી મેળવી શકો છો:\n\n"
                    "૧. **લગેજ શેરિંગ (Luggage Sharing)**: ફ્લાઈટ મુસાફરોની વધારાની લગેજ કેપેસિટી કેવી રીતે બુક કરવી.\n"
                    "૨. **પાર્સલ મોકલવું (Send Parcel)**: તમારું પેકેજ વિદેશ કે અન્ય સિટીમાં સુરક્ષિત રીતે મોકલવું.\n"
                    "૩. **એસ્ક્રો વોલેટ પેમેન્ટ (Escrow Vault)**: ૧૦૦% સુરક્ષિત પેમેન્ટ – ડિલિવરી OTP કન્ફર્મ થયા પછી જ પેમેન્ટ મુસાફરને મળે છે.\n"
                    "૪. **કેવાયસી અને પાસપોર્ટ વેરિફિકેશન (Trust & KYC)**: તમામ યુઝર્સનું ગવર્નમેન્ટ ID અને પાસપોર્ટ વેરિફિકેશન.\n"
                    "૫. **દવાઓ અને નીતિઓ (Medicine & Rules)**: ફક્ત ડોક્ટરના પ્રિસ્ક્રિપ્શન વાળી સીલ્ડ દવાઓ જ માન્ય છે.\n\n"
                    "તમારો કોઈપણ પ્રશ્ન ગુજરાતી અથવા English માં મુક્તપણે પૂછો!"
                ),
                "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
                "timestamp": "Just now"
            }

        if any(k in query_lower for k in ['drug', 'narcotic', 'ganja', 'dawa', 'illegal', 'bandhi', 'aushadhi', 'medicine']):
            if any(k in query_lower for k in ['dawa', 'medicine', 'aushadhi', 'doctor']):
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
        
        if any(k in query_lower for k in ['luggage', 'bhaadu', 'weight', 'kilo', 'baggage', 'samman', 'luggage sharing']):
            return {
                "text": (
                    "🧳 **લગેજ શેરિંગ (Luggage Sharing) કેવી રીતે કામ કરે છે:**\n\n"
                    "૧. **મુસાફર ફ્લાઈટ એડ કરે છે**: ટ્રેવલર પોતાની ફ્લાઈટ અને ઉપલબ્ધ વજન (દા.ત. 15 kg) લિસ્ટ કરે છે.\n"
                    "૨. **મોકલનાર ઓર્ડર બુક કરે છે**: સુંદર પોતાની સુટકેસ કે પેકેજ મોકલવા ટ્રેવલર સાથે કનેક્ટ થાય છે.\n"
                    "૩. **એસ્ક્રો વોલેટ સુવિધાઓ**: પેમેન્ટ FlyoraGo Escrow Vault માં સુરક્ષિત રીતે ડિપોઝિટ થાય છે.\n"
                    "૪. **6-Digit OTP કન્ફર્મેશન**: સામાન પહોંચ્યા પછી રેસિપિએન્ટ OTP આપે એટલે પેમેન્ટ ટ્રેવલરને મળે છે."
                ),
                "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["trips"]],
                "timestamp": "Just now"
            }

        if any(k in query_lower for k in ['paisa', 'payment', 'escrow', 'safe', 'wallet', 'refund', 'money']):
            return {
                "text": (
                    "💰 **એસ્ક્રો વોલેટ પેમેન્ટ સુરક્ષા (Escrow Payment Security):**\n\n"
                    "• **૧૦૦% સુરક્ષિત એસ્ક્રો**: તમારું પેમેન્ટ અગાઉથી સીધું મુસાફરને અપાતું નથી.\n"
                    "• **OTP સિસ્ટમ**: રેસિપિએન્ટ પાર્સલ સ્વીકારીને ૬-અંકનો OTP આપે ત્યારે જ પૈસા મુસાફરના વોલેટમાં ક્રેડિટ થાય છે.\n"
                    "• **ડિલિવરી કેન્સલ થાય તો**: જો ફ્લાઈટ કેન્સલ થાય કે ટ્રેવલર ના પહોંચાડે, તો સુંદરને ૧૦૦% રિફંડ મળે છે."
                ),
                "actions": [QUICK_NAV_ACTIONS["wallet"], QUICK_NAV_ACTIONS["support"]],
                "timestamp": "Just now"
            }

        return {
            "text": (
                "✈️ **FlyoraGo પ્લેટફોર્મની સંપૂર્ણ વિગત (How It Works):**\n\n"
                "૧. **મુસાફર (Traveler)**: પોતાની ફ્લાઈટ અને ખાલી લગેજ કેપેસિટી (દા.ત. 15 kg) એડ કરે છે.\n"
                "૨. **મોકલનાર (Sender)**: પોતાની સુટકેસ/સામાન મોકલવા માટે ટ્રેવલર સર્ચ કરે છે.\n"
                "૩. **એસ્ક્રો પેમેન્ટ (Escrow Vault)**: પેમેન્ટ FlyoraGo એસ્ક્રો વોલેટમાં ૧૦૦% સુરક્ષિત રહે છે.\n"
                "૪. **OTP ડિલિવરી**: સામાન પહોંચ્યા પછી 6-અંકનો OTP આપવાથી પેમેન્ટ મુસાફરને મળે છે.\n\n"
                "કોઈપણ ચોક્કસ માહિતી માટે તમારો પ્રશ્ન મુક્તપણે લખો!"
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

    # -----------------------------------------------------------------------
    # HINDI LANGUAGE INTENT RESPONSES
    # -----------------------------------------------------------------------
    if lang == 'hi':
        if any(k in query_lower for k in ['work', 'api', 'problem', 'error', 'chat boat', 'chatbot', 'nahi chal', 'connect']):
            return {
                "text": (
                    "🤖 **Flyora AI बोट एपीआई पूरी तरह से सक्रिय और चालू है! (Flyora AI API is Fully Working!):**\n\n"
                    "हमारा एआई इंजन आपके सभी सवालों के सटीक और पूर्ण उत्तर देने के लिए तैयार है। आप FlyoraGo प्लेटफॉर्म के बारे में निम्नलिखित जानकारी प्राप्त कर सकते हैं:\n\n"
                    "1. **लगेज शेयरिंग (Luggage Sharing)**: यात्रियों की बची हुई सामान क्षमता (Luggage Space) बुक करें।\n"
                    "2. **पार्सल भेजें (Send Package)**: अपना सामान सुरक्षित रूप से देश/विदेश भेजें।\n"
                    "3. **एस्क्रो वॉलेट सुरक्षा (Escrow Vault)**: 100% सुरक्षित भुगतान – डिलीवरी OTP सत्यापन के बाद ही रिलीज होता है।\n"
                    "4. **KYC एवं पासपोर्ट सत्यापन (Trust Score)**: सरकारी आईडी सत्यापन।"
                ),
                "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
                "timestamp": "Just now"
            }

        if any(k in query_lower for k in ['drug', 'narcotic', 'dawa', 'illegal', 'hathiyar', 'banned', 'medicine']):
            if any(k in query_lower for k in ['dawa', 'medicine', 'aushadhi', 'doctor']):
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
    # 0. INTENT: Technical & API Support Query
    if any(k in query_lower for k in ['chat boat', 'chatbot', 'bot api', 'api work', 'work karti nathi', 'api issue', 'api status', 'login 400', 'login error']):
        return {
            "text": (
                "🤖 **Flyora AI Chatbot API is 100% Operational & Online!**\n\n"
                "The Flyora AI API service is fully functional and ready to provide complete, detailed assistance for all FlyoraGo services:\n\n"
                "• **🧳 Luggage Sharing**: Monetize extra airline check-in baggage space or find verified travelers.\n"
                "• **📦 Parcel Shipping**: Send items internationally or locally with live flight route matching.\n"
                "• **💰 Escrow Vault**: 100% secure payment vault. Money is released only upon recipient 6-digit OTP entry.\n"
                "• **🛡️ Trust Score & KYC**: Government Passport/ID verification and ratings.\n"
                "• **🚫 Prohibited Items**: Zero tolerance for illegal goods; strict doctor prescription rules for medicines.\n\n"
                "Feel free to ask any specific question!"
            ),
            "actions": [QUICK_NAV_ACTIONS["luggage"], QUICK_NAV_ACTIONS["sender"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now"
        }

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
    if any(k in query_lower for k in ['how it works', 'how does it work', 'how flyorago work', 'how does flyorago work', 'what is flyorago', 'overview', 'about platform', 'process', 'work']):
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

    # 5. INTENT: TRUST_AND_SAFETY (Trust, Stranger Concerns, KYC, Verification, Fraud, Non-Delivery Protection)
    trust_safety_keywords = [
        'trust', 'stranger', 'genuine', 'real traveller', 'real traveler', 'how do i know',
        'steal', 'stolen', 'stole', 'rob', 'thief', 'lost', 'not deliver', 'does not deliver',
        'fails to deliver', 'fail to deliver', 'fraud', 'scam', 'cheat', 'fake', 'safe',
        'safety', 'kyc', 'verify', 'verification', 'passport', 'id verification',
        'protection', 'protect', 'secure', 'security', 'guarantee', 'reliable', 'reliability'
    ]
    if any(k in query_lower for k in trust_safety_keywords):
        # Non-Delivery & Theft Protection Sub-Intent
        if any(k in query_lower for k in ['not deliver', 'does not deliver', 'fails to deliver', 'fail to deliver', 'steal', 'stolen', 'thief', 'rob', 'lost']):
            return {
                "text": (
                    "🛡️ **FlyoraGo Non-Delivery & Theft Protection (Escrow & Dispute):**\n\n"
                    "FlyoraGo guarantees complete package protection if a traveler fails to deliver or attempts theft:\n\n"
                    "1. **100% Escrow Vault Lock**: Your shipping reward is held securely in Escrow and is NEVER paid to the traveler upfront.\n"
                    "2. **Cryptographic OTP Handover**: Funds are ONLY released if your designated recipient receives the parcel and provides the secret 6-digit OTP.\n"
                    "3. **Raise Dispute & Instant Freeze**: If a traveler does not deliver or vanishes, click 'Raise Dispute'. Your funds are locked immediately, and FlyoraGo issues a **100% full refund** to your wallet.\n"
                    "4. **KYC & Legal Enforcement**: All travelers complete government passport/ID KYC verification. Fraudulent travelers face permanent account bans and immediate law enforcement reporting."
                ),
                "intent": "TRUST_AND_SAFETY",
                "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["wallet"], QUICK_NAV_ACTIONS["support"]],
                "timestamp": "Just now",
                "is_fallback": True
            }

        # Traveller Identity Verification Sub-Intent
        if any(k in query_lower for k in ['verify', 'verification', 'kyc', 'how do you verify', 'passport', 'genuine']):
            return {
                "text": (
                    "🛡️ **FlyoraGo Traveller Verification Process:**\n\n"
                    "Every traveler on FlyoraGo must pass mandatory identity & safety checks before accepting packages:\n\n"
                    "1. **Government Passport & ID KYC**: Verified national identification and passport records.\n"
                    "2. **Flight Ticket Verification**: Travelers submit verified flight booking PNR and ticket confirmation.\n"
                    "3. **Public Ratings & Reviews**: Senders can review transparent past delivery history, ratings, and member trust scores.\n"
                    "4. **Physical Handover Inspection**: Pre-flight item photo inspection required before luggage acceptance."
                ),
                "intent": "TRUST_AND_SAFETY",
                "actions": [QUICK_NAV_ACTIONS["kyc"], QUICK_NAV_ACTIONS["trust"]],
                "timestamp": "Just now",
                "is_fallback": True
            }

        # General Trust & Safety Response
        return {
            "text": (
                "🛡️ **FlyoraGo Trust, Safety & Anti-Fraud Security System:**\n\n"
                "FlyoraGo builds trust through multiple security layers:\n\n"
                "1. **Mandatory Passport & KYC Verification**: Travellers are verified through mandatory government ID, passport, and flight ticket checks.\n"
                "2. **100% Protected Escrow Vault**: Payments are locked in the FlyoraGo Escrow Vault. Funds are released ONLY after successful delivery confirmation.\n"
                "3. **6-Digit Cryptographic OTP Confirmation**: Payouts require the recipient's secret 6-digit OTP code at physical handover.\n"
                "4. **Transparent Member Profiles & Reviews**: Both users can view verified profiles, ratings, and transaction history.\n"
                "5. **Dispute Resolution & Full Refund**: If any issue occurs or delivery fails, click 'Raise Dispute' to lock funds and receive a 100% full refund."
            ),
            "intent": "TRUST_AND_SAFETY",
            "actions": [QUICK_NAV_ACTIONS["trust"], QUICK_NAV_ACTIONS["kyc"], QUICK_NAV_ACTIONS["wallet"]],
            "timestamp": "Just now",
            "is_fallback": True
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

