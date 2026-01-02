from django.urls import path, include
from booking.views import BookingListAPIView, BookingViewSet, FlightViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'create-booking', BookingViewSet, basename='create-booking')
router.register(r'flights', FlightViewSet, basename='flights')
urlpatterns = [
    path('bookings/', BookingListAPIView.as_view(), name='booking-list'),
    path('', include(router.urls)),
]