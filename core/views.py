from django.shortcuts import  render, get_object_or_404
from rest_framework.generics import CreateAPIView, UpdateAPIView, GenericAPIView
from rest_framework import status 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Booking, Master, MasterAvailability
from .serializers import BookingCompleteSerializer, BookingCreateSerializer, BookingResponseSerializer, BookingMasterActionSerializer, BookingClientConfirmSerializer,  MasterCreateSerializer, MasterListSerializer, MasterAvailabilitySerializer
from core.utils import cancel_expired_bookings, calculate_distance_km, get_today_availability





class BookingCreateView(CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer

    def create(self, request, *args, **kwargs):
        cancel_expired_bookings() 
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        response_serializer = BookingResponseSerializer(booking)
        return Response(response_serializer.data, status=201)


class BookingMasterActionView(UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingMasterActionSerializer
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BookingClientConfirmAPIView(UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingClientConfirmSerializer
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        booking.client_confirmed = serializer.validated_data.get('client_confirmed', booking.client_confirmed)
        if booking.client_confirmed:
            booking.status = "confirmed"
        booking.save()

        return Response({
            "booking_id": booking.id,
            "status": booking.status
        })



class BookingCompleteAPIView(UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCompleteSerializer
    lookup_field = 'id'

    def patch(self, request, id):
        booking = get_object_or_404(Booking, id=id)

        serializer = BookingCompleteSerializer(
            booking,
            data={},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    


###### MASTER BOOKING LIST VIEW ##########


class TestAPIView(APIView):
    def get(self, request):
        return Response({
            "message": "Timey backend is working fine!"
        })
    

class MasterCreateAPIView(CreateAPIView): # master yaratish uchun
    queryset = Master.objects.all()
    serializer_class = MasterCreateSerializer




class MasterListAPIView(APIView): #masterlarni filterlab olish uchun
    def get(self, request):
        masters = Master.objects.all()

        # service_type boyicha filterlash
        service_type = request.query_params.get('service_type')
        if service_type: #agar service_type bolsa chiqar.
            masters = masters.filter(service_type=service_type)
        
        # distance boyicha filterlash
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        sort = request.query_params.get('sort')  # rating | distance | last_interacted

        if lat and lng and sort == 'distance':
            lat = float(lat)
            lng = float(lng)

            masters = sorted(
                masters,
                key=lambda m:calculate_distance_km(
                    lat, lng, m.location.lat, m.location.lng
                )
            )
        
        if sort == 'rating':
            masters = masters.order_by('-rating')


        only_available = request.query_params.get('only_available')

        if only_available == 'true':
            masters = [
                m for m in masters
                if get_today_availability(m)["is_available_today"]
            ]



        serializer = MasterListSerializer(
            masters, 
            many = True, 
            context={'request': request}
            )
        return Response(serializer.data)

    
class MasterAvailabilityUpdateAPIView(GenericAPIView):
        serializer_class = MasterAvailabilitySerializer

        def patch(self, request, master_id):
            master = get_object_or_404(Master, id=master_id)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            date = serializer.validated_data['date']

            availability, created = MasterAvailability.objects.update_or_create(
                master=master,
                date=date,
                defaults={
                    'available_slots': serializer.validated_data['available_slots'],
                    'discount_percent': serializer.validated_data.get('discount_percent', 0),
                }
            )

            return Response(
                {'success': True},
                status=status.HTTP_200_OK
        )
