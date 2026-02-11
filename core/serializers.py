import re
from rest_framework import serializers
from .models import Booking, Master, MasterLocation, MasterAvailability
from django.utils import timezone
from datetime import datetime
from core.utils import calculate_distance_km, get_master_availability


class EmptySerializer(serializers.Serializer):
    pass

class BookingCreateSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])

    class Meta:
        model = Booking
        fields = ['user_id', 'master_id', 'service_type', 'date', 'time', 'payment_type']

    def validate(self, data):
        date = data.get("date")
        time = data.get("time")
        booking_datetime = datetime.combine(date, time)
        booking_datetime = timezone.make_aware(booking_datetime, timezone.get_current_timezone())

        if booking_datetime < timezone.now():
            raise serializers.ValidationError("Booking time cannot be in the past.")

        # Ikki marta band qilishni oldini olish
        master_id = data.get("master_id")
        if Booking.objects.filter(
            master_id=master_id,
            date=date,
            time=time,
            status__in=["pending", "accepted", "confirmed"]
        ).exists():
            raise serializers.ValidationError("This time slot is already booked for the selected master.")

        return data

    def validate_time(self, value):
        return value.replace(second=0, microsecond=0)
    


class BookingResponseSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='id', read_only=True)
    status = serializers.CharField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = Booking
        fields = ['booking_id', 'status', 'expires_at', 'master_id', 'user_id']
    
    


class BookingMasterActionSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(read_only=True, source='id')
    reason = serializers.CharField(source='reject_reason', required=False, allow_null=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'status', 'reason']


    def validate(self, attrs):
        status_value = attrs.get('status')
        reason_value = attrs.get('reject_reason')

        if status_value == 'rejected' and not reason_value:
            raise serializers.ValidationError("Rejected qilganiz uchun sabab kiritishingiz kerak.")
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status == 'accepted':
            data.pop('reason', None)  
        return data


class BookingClientConfirmSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(read_only=True, source='id')
    status = serializers.CharField(read_only=True)
    client_confirmed = serializers.BooleanField(required=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'status', 'client_confirmed']

    def validate_client_confirmed(self, value):
        booking = self.instance
        if not booking:
            raise serializers.ValidationError("Booking topilmadi.")

        # Booking datetime ni yaratish
        booking_datetime = datetime.combine(booking.date, booking.time)
        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(booking_datetime, timezone.get_current_timezone())

        now = timezone.localtime()  # Hozirgi vaqtni localtime bilan olish
        time_diff = booking_datetime - now

        if time_diff.total_seconds() < 0:
            raise serializers.ValidationError("Bu buyurtma vaqti allaqachon o'tgan.")
        # if time_diff.total_seconds() > 60 * 60:
        #     raise serializers.ValidationError("Faqat buyurtmadan 60 daqiqa oldin tasdiqlashingiz mumkin.")
        if time_diff.total_seconds() < 30 * 60:
            raise serializers.ValidationError("Faqat buyurtmadan 30 daqiqa oldin tasdiqlashingiz mumkin.")

        return value





class BookingCompleteSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='id', read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'status']

    def validate(self, data):
        booking = self.instance

        if booking.status not in ['accepted', 'confirmed']:
            raise serializers.ValidationError( "Faqat qabul qilingan yoki tasdiqlangan buyurtmani tugatish mumkin.")

        return data

    def update(self, instance, validated_data):
        instance.status = 'completed'
        instance.save()
        return instance





########## MASTER BOOKING LIST SERIALIZER ##########



class MasterLocationSerializer(serializers.ModelSerializer): #master location uchun
    class Meta:
        model = MasterLocation
        fields = (
            'lat', 
            'lng', 
            'address', 
            'district', 
            'place_id', 
            'accuracy'
            )


class MasterCreateSerializer(serializers.ModelSerializer): #master yaratish uchun
    master_location = MasterLocationSerializer(write_only=True)
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    class Meta:
        model = Master
        fields = (
            'id',
            'full_name',
            'phone',
            'service_type',
            'service_types',
            'price',
            'experience_years',
            'about',
            'avatar_url',
            'status',
            'created_at',
            'master_location',
        )

        read_only_fields = ('id', 'status', 'created_at')
    
    def validate_service_types(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("service_types list bo'lishi kerak.")
        
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"service_types[{idx}] obyekt bo'lishi kerak.")
            if "name" not in item or not item["name"]:
                raise serializers.ValidationError(f"service_types[{idx}].name kerak.")
            if "service_price" not in item:
                raise serializers.ValidationError(f"service_types[{idx}].service_price kerak.")
            price = item["service_price"]
            if not isinstance(price, int) or price < 0:
                raise serializers.ValidationError(
                    f"service_types[{idx}].service_price musbat son bo'lishi kerak."
                    )
        return value




    def create(self, validated_data):
        location_data = validated_data.pop('master_location')

        master = Master.objects.create(**validated_data) #usta yaratiladi
        MasterLocation.objects.create(master=master, **location_data)
        return master
    

class MasterListSerializer(serializers.ModelSerializer): #masterlarni filterlab olish uchun
    master_location = MasterLocationSerializer(read_only=True)
    discount_percent = serializers.SerializerMethodField()
    is_available_today = serializers.SerializerMethodField()
    next_available_time = serializers.SerializerMethodField()
    rating = serializers.FloatField()
    id = serializers.SerializerMethodField()




    class Meta:
        model = Master
        fields = (
            'id',
            'full_name',
            'service_type',
            'price',
            'rating',
            'master_location',
            'discount_percent',
            'is_available_today',
            'next_available_time',
            
        )
        
    
    # master mavjudligi uchun
    def get_is_available_today(self, obj):
        from core.utils import get_today_availability
        return get_master_availability(obj)["is_available_today"]
    
    def get_next_available_time(self, obj):
        from core.utils import get_today_availability
        return get_master_availability(obj)["next_available_time"]
    
    def get_discount_percent(self, obj):
        from core.utils import get_today_availability
        return get_master_availability(obj)["discount_percent"]
    
    def get_id(self, obj):
        return str(obj.id).zfill(5)  # ID ni 5 ta raqamga to'ldirish


class MasterAvailabilitySerializer(serializers.ModelSerializer):
        class Meta:
            model = MasterAvailability
            fields = (
                'date',
                'available_slots',
                'discount_percent',
            )

class MasterDetailSerializer(serializers.ModelSerializer): #master detail uchun
    master_location = MasterLocationSerializer(read_only=True)
    discount_percent = serializers.SerializerMethodField()
    is_available_today = serializers.SerializerMethodField()
    next_available_time = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = Master
        fields = (
            'id',
            'full_name',
            'phone',
            'service_type',
            'service_types',
            'price',
            'experience_years',
            'rating',
            'avatar_url',
            'about',
            'master_location',
            'discount_percent',
            'is_available_today',
            'next_available_time',
        )

    def get_discount_percent(self, obj):
        return get_master_availability(obj)["discount_percent"]

    def get_is_available_today(self, obj)-> bool:
        return get_master_availability(obj)["is_available_today"]

    def get_next_available_time(self, obj) -> str | None:
        return get_master_availability(obj)["next_available_time"]

    def get_id(self, obj):
        return str(obj.id).zfill(5)









UZ_PHONE_RE = re.compile(r"^\+998\d{9}$")

class SendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        if not UZ_PHONE_RE.match(value):
            raise serializers.ValidationError("Phone must be in format +998XXXXXXXXX")
        return value


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(min_length=4, max_length=6)

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        if not UZ_PHONE_RE.match(value):
            raise serializers.ValidationError("Phone must be in format +998XXXXXXXXX")
        return value


class GuestCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    device_id = serializers.CharField(max_length=128)
    platform = serializers.ChoiceField(choices=["android", "ios", "web"])