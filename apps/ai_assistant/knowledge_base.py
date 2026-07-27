"""
Flyora AI Comprehensive Knowledge Base & Intent Classifier Engine
Provides intent classification, direct factual responses, prohibited items policy enforcement, and structured fallbacks.
"""

QUICK_NAV_ACTIONS = {
    "luggage": {"label": "Go to Luggage Sharing 🧳", "path": "/luggage-sharing"},
    "wallet": {"label": "Open My Wallet 💰", "path": "/wallet"},
    "sender": {"label": "Send a Package 📦", "path": "/sender"},
    "trips": {"label": "Publish a Flight Trip ✈️", "path": "/trips"},
    "trust": {"label": "Check Trust Score ⭐", "path": "/trust"},
    "kyc": {"label": "Verify Identity / KYC 🛡️", "path": "/kyc"},
    "support": {"label": "Customer Support 💬", "path": "/support"}
}


def classify_intent_and_respond(prompt_text: str, user_context: dict = None, history: list = None, db_items: list = None) -> dict:
    """
    Analyzes exact user query intent and returns direct, non-promotional, policy-compliant responses.
    """
    query = prompt_text.lower().strip()
    actions = []

    # Check custom DB items first if matching keywords exist
    if db_items:
        for item in db_items:
            if item.get('is_active') and item.get('question', '').lower() in query:
                return {
                    "text": item.get('answer'),
                    "actions": [QUICK_NAV_ACTIONS["support"]],
                    "timestamp": "Just now"
                }

    # 1. INTENT: Prohibited Items & Illegal Goods (Drugs, Weapons, Contraband)
    if any(k in query for k in ['drug', 'drugs', 'narcotic', 'weed', 'weapon', 'gun', 'knife', 'explosive', 'illegal', 'contraband', 'banned', 'restricted', 'smuggle']):
        response_text = (
            "🚫 **Prohibited Items Policy & Safety Rules:**\n\n"
            "FlyoraGo strictly prohibits the transport or sharing of any illegal or dangerous items, including:\n"
            "• **Drugs & Narcotics**: Illegal substances, prescription drugs without owner authorization, or controlled narcotics.\n"
            "• **Weapons & Explosives**: Firearms, ammunition, knives, fireworks, or hazardous chemical agents.\n"
            "• **Restricted Contraband**: Undeclared currency over legal limits, counterfeit goods, or protected wildlife items.\n\n"
            "**Enforcement & Consequences:**\n"
            "1. **Mandatory Inspection**: Travelers inspect and photograph all package contents before accepting physical custody.\n"
            "2. **Immediate Rejection**: Any suspicious or prohibited package is rejected instantly.\n"
            "3. **Account Suspension & Law Enforcement**: Accounts attempting to ship prohibited items are permanently banned and reported to aviation authorities."
        )
        actions.append(QUICK_NAV_ACTIONS["trust"])
        actions.append(QUICK_NAV_ACTIONS["kyc"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 2. INTENT: How FlyoraGo Works (Platform Overview)
    elif any(k in query for k in ['how it works', 'how does it work', 'what is flyorago', 'overview', 'about platform']):
        response_text = (
            "✈️ **How FlyoraGo Works:**\n\n"
            "FlyoraGo connects verified international travelers who have unused luggage capacity with senders who need packages delivered securely.\n\n"
            "**Platform Workflow:**\n"
            "1. **Publish Flight Trip**: Traveler publishes flight route, airline, and available baggage weight (e.g. 15 KG).\n"
            "2. **Search & Request**: Sender finds matching flight routes and submits a package transport request.\n"
            "3. **Traveler Acceptance**: Traveler reviews package photos/weight and accepts the request.\n"
            "4. **Escrow Security**: Sender deposits payment into **FlyoraGo Escrow Vault**.\n"
            "5. **Physical Pickup**: Traveler inspects physical contents and uploads handover photos.\n"
            "6. **OTP Handover**: Upon arrival, recipient provides a **6-Digit OTP** to release escrow payment to the traveler."
        )
        actions.append(QUICK_NAV_ACTIONS["luggage"])
        actions.append(QUICK_NAV_ACTIONS["sender"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 3. INTENT: Traveller Earning & Income Workflow
    elif any(k in query for k in ['earn', 'earning', 'income', 'make money', 'traveller income', 'reward price', 'payout timeline']):
        response_text = (
            "💰 **Traveller Earning & Payment Release Workflow:**\n\n"
            "Travelers monetize unused airline check-in baggage space by carrying verified parcels on their flight route.\n\n"
            "**How Earnings Work:**\n"
            "• **Set Your Rates**: Set agreed reward rates per KG (e.g. $10 - $25 per KG).\n"
            "• **100% Escrow Hold**: Upon accepting a request, sender funds are locked in Escrow before flight departure.\n"
            "• **Instant Release**: After flight landing, the recipient enters the **6-Digit OTP code** or scans QR code at handover, which instantly transfers earnings to your Flyora Wallet for bank or UPI withdrawal."
        )
        actions.append(QUICK_NAV_ACTIONS["trips"])
        actions.append(QUICK_NAV_ACTIONS["wallet"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 4. INTENT: Sender Delivery & Tracking Workflow
    elif any(k in query for k in ['send package', 'sender workflow', 'track delivery', 'shipping steps', 'package request']):
        response_text = (
            "📦 **Sender Package Delivery Workflow:**\n\n"
            "1. **Create Request**: Enter package weight, dimensions, departure/destination cities.\n"
            "2. **Match Traveler**: Select from verified travelers flying your exact flight route.\n"
            "3. **Deposit Escrow**: Deposit shipping reward safely into Escrow Hold.\n"
            "4. **Handover Inspection**: Meet traveler at airport/city point for physical inspection & photo upload.\n"
            "5. **Track Flight**: Track transit status updates (In Transit, Arrived, Out for Delivery).\n"
            "6. **Confirm Delivery**: Provide recipient with the **6-Digit OTP** to complete handover."
        )
        actions.append(QUICK_NAV_ACTIONS["sender"])
        actions.append(QUICK_NAV_ACTIONS["trips"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 5. INTENT: Safety, Security, Fraud Prevention & KYC
    elif any(k in query for k in ['security', 'safety', 'kyc', 'fraud', 'verify', 'passport', 'id verification', 'scam']):
        response_text = (
            "🛡️ **Safety, Security & Anti-Fraud Protection:**\n\n"
            "• **Mandatory Passport & National ID KYC**: All senders and travelers are multi-step identity verified.\n"
            "• **Physical Inspection**: Travelers must inspect package contents and upload verification photos before flight departure.\n"
            "• **100% Escrow Protection**: Senders never pay travelers directly. Escrow holds funds safely until delivery is confirmed.\n"
            "• **Cryptographic OTP Handover**: 6-digit cryptographic OTP verification prevents false delivery claims."
        )
        actions.append(QUICK_NAV_ACTIONS["kyc"])
        actions.append(QUICK_NAV_ACTIONS["trust"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 6. INTENT: Payments, Escrow & Wallet Withdrawal
    elif any(k in query for k in ['payment', 'escrow', 'wallet', 'withdraw', 'refund', 'cancellation']):
        response_text = (
            "💳 **Payments, Escrow & Refund Policy:**\n\n"
            "• **Escrow Lock**: Funds are locked upon booking acceptance and protected throughout flight transit.\n"
            "• **Instant Release**: Released to traveler wallet upon valid 6-digit OTP code entry.\n"
            "• **Full Refund Guarantee**: Senders receive a 100% full escrow refund if a trip is cancelled or traveler fails parcel verification."
        )
        actions.append(QUICK_NAV_ACTIONS["wallet"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 7. INTENT: Disputes & Customer Support
    elif any(k in query for k in ['dispute', 'damage', 'missing', 'late', 'complaint', 'claim', 'support']):
        response_text = (
            "⚠️ **Dispute Resolution & Customer Support:**\n\n"
            "If a parcel is damaged, delayed, or unverified at handover:\n"
            "1. **Raise Dispute**: Click 'Raise Dispute' on the booking details page before revealing the OTP code.\n"
            "2. **Escrow Frozen**: Escrow funds are frozen immediately pending admin investigation.\n"
            "3. **Admin Review**: Support team inspects handover photos, weight receipts, and chat logs to resolve claims fairly."
        )
        actions.append(QUICK_NAV_ACTIONS["support"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}

    # 8. STRUCTURED FALLBACK FOR AMBIGUOUS / UNCLEAR QUERIES
    else:
        response_text = (
            "I can help you with FlyoraGo! Are you asking about:\n\n"
            "1. **How Luggage Sharing Works** (Baggage weight marketplace)\n"
            "2. **Traveller Earning Process** (How travelers monetize unused capacity)\n"
            "3. **Package Safety & Prohibited Items Rules** (Drugs, contraband & safety policies)\n"
            "4. **Payment, Escrow & Wallet Release** (How funds are protected)\n\n"
            "Please type one of the topics above or ask a specific question!"
        )
        actions.append(QUICK_NAV_ACTIONS["luggage"])
        actions.append(QUICK_NAV_ACTIONS["sender"])
        return {"text": response_text, "actions": actions, "timestamp": "Just now"}
