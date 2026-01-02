from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from booking.models import Booking, Flight
from booking.serializers import BookingSerializer, CreateBookingSerializer, FlightSerializer
from booking.helpers import is_seat_available, transition_booking_status, mock_payment_processing

# Create your views here.
class FlightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer


class BookingListAPIView(ListAPIView):
    queryset = Booking.objects.select_related('flight').all().order_by('-created_at')
    serializer_class = BookingSerializer


class BookingViewSet(mixins.CreateModelMixin,mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    queryset = Booking.objects.select_related('flight').all()
    serializer_class = BookingSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateBookingSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            flight = Flight.objects.select_for_update().get(pk=serializer.validated_data['flight'].pk)
            if flight.available_seats <= 0:
                return Response({'flight': 'This flight is fully booked.'}, status=status.HTTP_400_BAD_REQUEST)
            seat_number = serializer.validated_data['seat_number']
            if not is_seat_available(seat_number, flight):
                return Response({'seat_number': f'Seat {seat_number} is already booked. Please choose another.'}, status=status.HTTP_400_BAD_REQUEST)
            booking = serializer.save()
            try:
                booking = transition_booking_status(booking, 'SEAT_HELD')
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            flight.available_seats -= 1
            flight.save()
        response_serializer = BookingSerializer(booking)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        booking = self.get_object()
        if not booking.status in ['SEAT_HELD', 'PAYMENT_PENDING']:
            return Response({'error': 'Payment can only be processed.'}, status=status.HTTP_400_BAD_REQUEST)
        if booking.hold_expires_at and booking.hold_expires_at < timezone.now():
            return Response({'error': 'Booking has expired. Please create a new booking.'}, status=status.HTTP_400_BAD_REQUEST)
        if booking.status == 'SEAT_HELD':
            try:
                transition_booking_status(booking, 'PAYMENT_PENDING')
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        payment_successful = mock_payment_processing()
        if not payment_successful:
            return Response({'error': 'Payment failed. Please try again.'}, status=status.HTTP_402_PAYMENT_REQUIRED)
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking.pk)
            if booking.status != 'PAYMENT_PENDING':
                return Response({'error': 'Booking status has changed. Please retry.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                booking = transition_booking_status(booking, 'CONFIRMED')
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status != 'CONFIRMED':
            return Response({'error': 'Only CONFIRMED bookings can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking.pk)
            try:
                booking = transition_booking_status(booking, 'CANCELLED')
                booking = transition_booking_status(booking, 'REFUNDED')
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
