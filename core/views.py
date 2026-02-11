from email.mime import text
from core.sms import eskiz_send_sms
from django.shortcuts import  render, get_object_or_404
from rest_framework.generics import CreateAPIView, UpdateAPIView, GenericAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import status 

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booking, Master, MasterAvailability, OTP, GuestProfile
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
import random
from datetime import timedelta
from .serializers import(BookingCompleteSerializer, BookingCreateSerializer, BookingResponseSerializer, 
                        BookingMasterActionSerializer, BookingClientConfirmSerializer, EmptySerializer,  MasterCreateSerializer,
                        MasterListSerializer, MasterAvailabilitySerializer, SendOtpSerializer, VerifyOtpSerializer,
                        GuestCreateSerializer, MasterDetailSerializer)
from core.utils import cancel_expired_bookings, get_today_availability, get_next_available_time





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
    


class BookingListAPIView(GenericAPIView):
    serializer_class = BookingResponseSerializer

    def get_queryset(self):
        queryset = Booking.objects.all()

        status_param = self.request.query_params.get("status")
        master_id = self.request.query_params.get("master_id")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if master_id:
            queryset = queryset.filter(master_id=master_id)

        return queryset

    def get(self, request, *args, **kwargs):
        bookings = self.get_queryset()
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)


###### MASTER BOOKING LIST VIEW ##########
class TestAPIView(APIView):
    serializer_class = EmptySerializer
    def get(self, request):
        return Response({
            "message": "Timey backend is working fine!"
        })
    

class MasterCreateAPIView(CreateAPIView): # master yaratish uchun
    queryset = Master.objects.all()
    serializer_class = MasterCreateSerializer



@extend_schema(
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Sahifa raqami (1,2,3...)"),
        OpenApiParameter("size", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Har sahifada nechta master"),
        OpenApiParameter("service_type", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Masalan: barber"),
        OpenApiParameter("only_available", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="true bo‘lsa faqat bo‘shlar"),
        OpenApiParameter("sort", OpenApiTypes.STR, OpenApiParameter.QUERY, description="rating bo‘yicha tartib"),
    ]
)
class MasterListAPIView(APIView):
    serializer_class = EmptySerializer #masterlarni filterlab olish uchun
    def get(self, request):
        masters = Master.objects.all()

        # service_type boyicha filterlash
        service_type = request.query_params.get('service_type', 'barber')
        masters = masters.filter(service_type=service_type)

        # faqat mavjud bo'lganlarni olish
        only_available = request.query_params.get('only_available')
        if only_available == 'true':
            masters = [
                m for m in masters
                if get_today_availability(m)["is_available_today"]
            ]
        
        #sort boyicha tartiblash
        sort = request.query_params.get('sort')
        if sort == 'rating':
            masters = masters.order_by('-rating')


        #pagination
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 5))

        total = len(masters) if isinstance(masters, list) else masters.count()
        start = (page - 1) * size
        end = start + size

        masters_page = masters[start:end]



        serializer = MasterListSerializer(
            masters_page, 
            
            many = True, 
            context={'request': request}
            )
        
        return Response({
            "page": page,
            "size": size,
            "total": total,
            "results": serializer.data
        })
    
#
class MasterAvailabilityPatchAPIView(GenericAPIView):
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


#master detail uchun
class MasterDetailAPIView(RetrieveAPIView):
    queryset = Master.objects.all()
    serializer_class = MasterDetailSerializer
    lookup_field = 'id'  


#master keyingi mavjud vaqtni olish uchun
class MasterNextAvailableTimeAPIView(APIView):
    def get(self, request, master_id):
        master = get_object_or_404(Master, id=master_id)
        next_time = get_next_available_time(master)

        return Response({
            "master_id": str(master.id).zfill(5),
            "next_available_time": next_time
        })







### MASTER MODEL AUTH OTP VIEWs ###

from .sms import eskiz_send_sms

OTP_EXPIRES_SECONDS = 120
OTP_RESEND_AFTER_SECONDS = 60
ACCESS_EXPIRES_SECONDS = 900  # 15 minut (clientga ko'rsatish uchun)


def generate_otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"


class MasterSendOtpAPIView(GenericAPIView):
    serializer_class = SendOtpSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data.get("request", request.data))
        ser.is_valid(raise_exception=True)

        phone = ser.validated_data["phone"]
        now = timezone.now()

        last_otp = OTP.objects.filter(phone=phone, is_used=False).order_by("-created_at").first()
        if last_otp and now < last_otp.resend_available_at:
            wait_seconds = int((last_otp.resend_available_at - now).total_seconds())
            return Response(
                {
                    "success": False,
                    "message": f"Please wait {wait_seconds} seconds before resending",
                    "resend_after": wait_seconds,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = generate_otp_code()

        OTP.objects.create(
            phone=phone,
            code=code,
            expires_at=now + timedelta(seconds=OTP_EXPIRES_SECONDS),
            resend_available_at=now + timedelta(seconds=OTP_RESEND_AFTER_SECONDS),
        )

        text = f"Timey tasdiqlash kodi: {code}"

        
        eskiz_send_sms(phone, text)

        
        return Response(
            {
                "success": True,
                "message": "SMS code sent",
                "expires_in": OTP_EXPIRES_SECONDS,
                "resend_after": OTP_RESEND_AFTER_SECONDS,
                "code": code,  
            },
            status=status.HTTP_200_OK,
        )


class MasterVerifyOtpAPIView(GenericAPIView):
    serializer_class = VerifyOtpSerializer
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data.get("request", request.data))
        ser.is_valid(raise_exception=True)

        phone = ser.validated_data["phone"]
        code = ser.validated_data["code"]
        now = timezone.now()

        otp = (
            OTP.objects
            .select_for_update()
            .filter(phone=phone, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return Response(
                {"success": False, "message": "Invalid code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if now >= otp.expires_at:
            return Response(
                {"success": False, "message": "Code expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✔ OTP ishlatildi
        otp.is_used = True
        otp.save(update_fields=["is_used"])

        
        master, created = Master.objects.get_or_create(
            phone=phone,
            defaults={
                "full_name": "New Master",
                "service_type": "unknown",
                "experience_years": 0,
                "rating": 0,
                "status": "active",
            },
        )

     
        refresh = RefreshToken.for_user(master)

        return Response(
            {
                "success": True,
                "master": {
                    "id": str(master.id).zfill(5),
                    "phone": master.phone,
                    "role": "master",
                    "status": getattr(master, "status", "active"),
                },
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "expires_in": ACCESS_EXPIRES_SECONDS,
            },
            status=status.HTTP_200_OK,
        )




### USER MODEL AUTHORIZED TELEGRAM PROFILE VIEW ###


class GuestUserCreateAPIView(GenericAPIView):
    serializer_class = GuestCreateSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data.get("request", request.data))
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        device_id = data["device_id"]

        # device_id bo‘yicha topamiz
        profile = GuestProfile.objects.filter(device_id=device_id).select_related("user").first()

        if not profile:
            # yangi guest user
            username = f"guest_{device_id}"[:150]
            user = User.objects.create(username=username)
            user.set_unusable_password()
            user.save()

            profile = GuestProfile.objects.create(user=user,device_id=device_id,platform=data["platform"],name=data["name"],city=data["city"])
        else:
            # mavjud guestni update
            profile.platform = data["platform"]
            profile.name = data["name"]
            profile.city = data["city"]
            profile.save(update_fields=["platform", "name", "city"])

        refresh = RefreshToken.for_user(profile.user)

        return Response(
            {
                "guest_user_id": f"guest_{profile.id}",
                "access_token": str(refresh.access_token),
                "role": "guest",
            },
            status=status.HTTP_200_OK,
        )