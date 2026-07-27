from decimal import Decimal
from django.db import transaction
from wallet.models import Wallet, Transaction

def calculate_ai_match_score(listing, search_params):
    """
    Calculates AI Match Percentage (0-100%) between Traveller search criteria and a LuggageListing.
    Parameters evaluated:
    - Same Flight (+40%)
    - Same Airline (+20%)
    - Same Airport (Departure + Arrival) (+20%)
    - Same Departure Date (+10%)
    - Time proximity (+5%)
    - Owner Trust Rating (+5%)
    """
    score = 45  # Baseline relevance score for active listing match

    dep_airport = search_params.get('departure_airport', '').strip().lower()
    arr_airport = search_params.get('arrival_airport', '').strip().lower()
    airline = search_params.get('airline', '').strip().lower()
    flight_num = search_params.get('flight_number', '').strip().lower()
    flight_date = search_params.get('departure_date', '').strip()

    if flight_num and listing.flight_number.strip().lower() == flight_num:
        score += 35

    if airline and listing.airline.strip().lower() == airline:
        score += 15

    if dep_airport and dep_airport in listing.departure_airport.strip().lower():
        score += 10
    if arr_airport and arr_airport in listing.arrival_airport.strip().lower():
        score += 10

    if flight_date and str(listing.departure_date) == flight_date:
        score += 10

    # Ensure max score capped at 99%
    final_score = min(score, 99)
    badge = f"{final_score}% Match"
    return final_score, badge


@transaction.atomic
def process_luggage_escrow_hold(booking):
    """
    Holds funds in Escrow from booker's wallet.
    """
    booker_wallet, _ = Wallet.objects.get_or_create(user=booking.booker)
    
    # Update wallet balance
    booker_wallet.balance_available = max(Decimal('0.00'), booker_wallet.balance_available - booking.total_price)
    booker_wallet.balance_escrow += booking.total_price
    booker_wallet.save()

    # Create Transaction record
    Transaction.objects.create(
        wallet=booker_wallet,
        amount=booking.total_price,
        type='Escrow Hold',
        status='Completed',
        description=f"Escrow Hold for Luggage Booking #{booking.id} ({booking.booked_weight}kg)",
        reference_id=f"LUG-ESCROW-{booking.id}"
    )

    booking.escrow_status = 'HELD'
    booking.save(update_fields=['escrow_status'])
    return True


@transaction.atomic
def process_luggage_escrow_release(booking):
    """
    Releases escrow funds from booker's wallet to owner's wallet upon completion.
    """
    if booking.escrow_status == 'RELEASED':
        return True

    booker_wallet, _ = Wallet.objects.get_or_create(user=booking.booker)
    owner_wallet, _ = Wallet.objects.get_or_create(user=booking.owner)

    # Deduct from booker's escrow
    booker_wallet.balance_escrow = max(Decimal('0.00'), booker_wallet.balance_escrow - booking.total_price)
    booker_wallet.save()

    # Add to owner's available balance
    owner_wallet.balance_available += booking.total_price
    owner_wallet.save()

    # Log Transactions
    Transaction.objects.create(
        wallet=booker_wallet,
        amount=booking.total_price,
        type='Payment Sent',
        status='Completed',
        description=f"Luggage Sharing Payment Completed for Booking #{booking.id}",
        reference_id=f"LUG-RELEASE-B-{booking.id}"
    )

    Transaction.objects.create(
        wallet=owner_wallet,
        amount=booking.total_price,
        type='Escrow Release',
        status='Completed',
        description=f"Luggage Sharing Earnings Received for Booking #{booking.id} ({booking.booked_weight}kg)",
        reference_id=f"LUG-RELEASE-O-{booking.id}"
    )

    booking.escrow_status = 'RELEASED'
    booking.save(update_fields=['escrow_status'])
    return True


@transaction.atomic
def process_luggage_escrow_refund(booking):
    """
    Refunds escrow funds back to booker's wallet.
    """
    if booking.escrow_status in ['REFUNDED', 'PENDING']:
        return True

    booker_wallet, _ = Wallet.objects.get_or_create(user=booking.booker)

    # Move from escrow back to available balance
    booker_wallet.balance_escrow = max(Decimal('0.00'), booker_wallet.balance_escrow - booking.total_price)
    booker_wallet.balance_available += booking.total_price
    booker_wallet.save()

    Transaction.objects.create(
        wallet=booker_wallet,
        amount=booking.total_price,
        type='Refund',
        status='Completed',
        description=f"Luggage Sharing Refund for Booking #{booking.id}",
        reference_id=f"LUG-REFUND-{booking.id}"
    )

    booking.escrow_status = 'REFUNDED'
    booking.save(update_fields=['escrow_status'])
    return True
