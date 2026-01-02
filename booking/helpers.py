import re
import random
import time
from datetime import timedelta
from django.utils import timezone
from booking.models import Booking, Flight
from django.db import transaction

def is_valid_seat_number(seat_number, flight):
    """Check if the seat number is valid (e.g 'A1', 'B12').
     args:
        seat_number: str - The seat number to validate.
        flight: Flight - The flight Object
    returns:
        bool - True if the seat number is valid, False otherwise.
    """
    if not seat_number or not flight:
        return False
    seat_number = seat_number.upper().strip()
    valid_seat_pattern = r'^(\d+)([A-Z])$'
    match = re.match(valid_seat_pattern, seat_number)
    if not match:
        return False
    seat_row = int(match.group(1))
    seat_column = match.group(2)
    if seat_row < 1 or seat_row > flight.total_seats_rows:
        return False
    if seat_column not in flight.seat_configuration:
        return False
    return True

def is_seat_available(seat_number, flight):
    """Check if the seat number is available for booking.
     args:
        seat_number: str - The seat number to check.
        flight: Flight - The flight Object
    returns:
        bool - True if the seat number is available, False otherwise.
    """
    if not is_valid_seat_number(seat_number, flight):
        return False
    seat_number = seat_number.upper().strip()
    booked_seats = Booking.objects.filter(
        flight=flight,
        seat_number=seat_number,
        status__in=['SEAT_HELD', 'PAYMENT_PENDING', 'CONFIRMED']
    ).exists()
    return not booked_seats


def can_transition_status(current_status, new_status):
    """Check if the booking can transition from current_status to new_status.
     args:
        current_status: str - The current status of the booking.
        new_status: str - The desired new status of the booking.
    returns:
        bool - True if the transition is valid, False otherwise
    """
    valid_transitions = {
        'INITIATED': ['SEAT_HELD'],
        'SEAT_HELD': ['PAYMENT_PENDING', 'EXPIRED'],
        'PAYMENT_PENDING': ['CONFIRMED', 'EXPIRED'],
        'CONFIRMED': ['CANCELLED'],
        'CANCELLED': ['REFUNDED'],
        'EXPIRED': [],
        'REFUNDED': [],
    }
    return new_status in valid_transitions.get(current_status, [])

def transition_booking_status(booking, new_status):
    """Transition the booking to a new status if valid.
     args:
        booking: Booking - The booking object to transition.
        new_status: str - The desired new status.
    returns:
        updated_booking object or raises exception if invalid.
    """
    if not can_transition_status(booking.status, new_status):
        raise Exception(f"Invalid status transition from {booking.status} to {new_status}")
    
    with transaction.atomic():
        update_booking = Booking.objects.select_for_update().get(pk=booking.pk)
        if not update_booking.status == booking.status:
            raise Exception("Booking status has changed, please retry.")
        update_booking.status = new_status
        if new_status == 'SEAT_HELD':
            update_booking.hold_expires_at = timezone.now() + timedelta(minutes=10)
        if new_status == 'CONFIRMED':
            update_booking.hold_expires_at = None
        if new_status in ['EXPIRED', 'REFUNDED']:
            flight_object = Flight.objects.select_for_update().get(pk=update_booking.flight.pk)
            flight_object.available_seats += 1
            flight_object.save()
        update_booking.save()
        return update_booking


def mock_payment_processing(success_rate=0.9, delay=True):
    """Mock payment processing function.
     args:
        success_rate: float - Probability of payment success (0.0 to 1.0).
        delay: bool - Whether to simulate processing delay.
    returns:
        bool - True if payment is successful, False otherwise.
    """
    if delay:
        delay_time = random.uniform(2, 5)
        time.sleep(delay_time)
        
    return random.random() < success_rate
        