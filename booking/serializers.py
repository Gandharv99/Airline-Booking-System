from rest_framework import serializers
from booking.helpers import is_seat_available, is_valid_seat_number
from booking.models import Booking, Flight

class FlightSerializer(serializers.ModelSerializer):
    total_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = ['id', 'flight_number', 'departure', 'arrival', 'departure_time', 'arrival_time', 'total_seats', 'seat_configuration', 'available_seats', 'created_at', 'updated_at']
        read_only_fields = fields

class BookingSerializer(serializers.ModelSerializer):
    flight = FlightSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = ['id', 'flight', 'passenger_name', 'passenger_email', 'seat_number', 'status', 'hold_expires_at', 'created_at', 'updated_at']
        read_only_fields = fields

class CreateBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['flight', 'passenger_name', 'passenger_email', 'seat_number']
    
    def validate(self, data):
        flight = data.get('flight')
        seat_number = data.get('seat_number').upper().strip()
        data['seat_number'] = seat_number

        if not data['passenger_name'] or len(data['passenger_name'].strip()) < 2:
            raise serializers.ValidationError({'passenger_name': 'Passenger name is required.'})
        
        if not is_valid_seat_number(seat_number, flight):
            raise serializers.ValidationError({
                'seat_number': 'Invalid seat number for this flight.'
            })
        
        if not is_seat_available(seat_number, flight):
            raise serializers.ValidationError({
                'seat_number': f'Seat {seat_number} is already booked. Please choose another.'
            })
        
        if flight.available_seats <= 0:
            raise serializers.ValidationError({
                'flight': 'This flight is fully booked.'
            })
        
        return data
    

        