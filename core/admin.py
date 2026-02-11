from django.contrib import admin

from core.models import OTP, Booking, GuestProfile, Master, MasterAvailability, MasterLocation, User

# Register your models here.


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'master_id', 'service_type', 'date', 'time', 'status', 'payment_type', 'created_at')
    list_filter = ('status', 'payment_type', 'date')
    search_fields = ('user_id', 'master_id', 'service_type')
    ordering = ('-created_at',)


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'created_at')
    search_fields = ('full_name', 'phone')
    ordering = ('-created_at',)



@admin.register(MasterLocation)
class MasterLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'master_id', 'lat', 'lng')
    search_fields = ('master_id',)
 


@admin.register(MasterAvailability)
class MasterAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'master_id', 'date', 'available_slots', 'discount_percent', 'created_at')
    search_fields = ('master_id', 'date')
    ordering = ('-created_at',)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'code', 'created_at')
    search_fields = ('phone',)
    ordering = ('-created_at',)


@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'created_at')
    search_fields = ('user_id',)
    ordering = ('-created_at',)


