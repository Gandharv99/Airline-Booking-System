from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Flight(models.Model):
    flight_number = models.CharField(max_length=10, unique=True)
    departure = models.CharField(max_length=100)
    arrival = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    total_seats_rows = models.IntegerField()
    seat_configuration = models.CharField(max_length=10)  # e.g., "ABCDEF"
    available_seats = models.IntegerField(editable=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.flight_number
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_seats = self.total_seats_rows * len(self.seat_configuration)
        return super().save(*args, **kwargs)

    @property
    def total_seats(self):
        return self.total_seats_rows * len(self.seat_configuration)
    
class Booking(models.Model):
    STATUS_CHOICES = [
        ('INITIATED', 'INITIATED'),
        ('SEAT_HELD', 'SEAT_HELD'),
        ('PAYMENT_PENDING', 'PAYMENT_PENDING'),
        ('CONFIRMED', 'CONFIRMED'),
        ('CANCELLED', 'CANCELLED'),
        ('EXPIRED', 'EXPIRED'),
        ('REFUNDED', 'REFUNDED'),
    ]
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    passenger_name = models.CharField(max_length=100)
    passenger_email = models.EmailField()
    seat_number = models.CharField(max_length=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['flight', 'seat_number', 'status'])]

    def __str__(self):
        return f"{self.passenger_name} - {self.flight.flight_number} - {self.seat_number} ({self.status})"
    
    