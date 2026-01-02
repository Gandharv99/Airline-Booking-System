from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from booking.models import Booking
from django.db import transaction
from booking.helpers import transition_booking_status

def expire_hold_bookings():
    """Function to expire bookings with SEAT_HELD status whose hold_expires_at has passed."""
    now = timezone.now()
    expired_bookings = Booking.objects.select_related('flight').filter(status__in=['SEAT_HELD', 'PAYMENT_PENDING'], hold_expires_at__lt=now)
    for booking in expired_bookings:
        try:
            with transaction.atomic():
                booking_refresh = Booking.objects.select_related('flight').select_for_update().get(pk=booking.pk)
                if booking_refresh.status in ['SEAT_HELD', 'PAYMENT_PENDING']:
                    transition_booking_status(booking_refresh, 'EXPIRED')
                    print(f"Expired booking {booking_refresh.id} for seat {booking_refresh.seat_number} on flight {booking_refresh.flight.flight_number}")
        except Exception as e:
            print(f"Error expiring booking {booking.id}: {str(e)}")
            continue
    
def start_scheduler():
    """Start the background scheduler to run the expire_hold_bookings job periodically."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(expire_hold_bookings, 'interval', seconds=60, id='expire_hold_bookings_job', replace_existing=True)
    scheduler.start()
    print("Scheduler started to expire hold bookings every 60 seconds.")