from django.apps import AppConfig
import sys


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):
        if 'runserver' in sys.argv:
            from booking.scheduler import start_scheduler
            start_scheduler()