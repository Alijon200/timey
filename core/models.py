from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
# Create your models here.

User = get_user_model()

def default_expires_at():
    return timezone.now() + timedelta(minutes=15)

class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    CONFIRMED = 'confirmed', 'Confirmed'
    CLIENT_NOT_CONFIRMED = 'client_not_confirmed', 'Client not confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'


class PaymentType(models.TextChoices):
    CASH = 'cash', 'Cash'
    CARD = 'card', 'Card'





class Booking(models.Model):
    user_id = models.PositiveIntegerField()    
    master_id = models.PositiveIntegerField()

    service_type = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()

    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,    
        default=PaymentType.CARD
    )

    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    expires_at = models.DateTimeField(null=False)
    reject_reason = models.TextField(null=True, blank=True)
    client_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            dt = datetime.combine(self.date, self.time)          # 2026-02-05 23:00
            aware_dt = timezone.make_aware(dt)                   # timezone-aware
            self.expires_at = aware_dt + timedelta(minutes=15)   # 23:15
        super().save(*args, **kwargs)




######### MASTER MODEL #############

class Master(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    )
    SERVICE_TYPES = (
        ('barber', 'Barber'),
        ('beard', 'Beard'),
        ('haircut', 'Haircut'),
        ('planting', 'Planting'),

    )

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='barber')
    service_types = models.JSONField(default=list, blank=True)  # Usta bir nechta xizmat ko‘rsatishi mumkin
    price = models.PositiveIntegerField(default=0)  # xizmat narxi
    experience_years = models.PositiveIntegerField()
    rating = models.FloatField(default=0)

    about = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class MasterLocation(models.Model):
    master = models.OneToOneField(
        Master,
        on_delete=models.CASCADE,
        related_name='master_location'
    )
    lat = models.FloatField()  #latitude- kenglik
    lng = models.FloatField()  #longitude-uzunlik
    address = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    place_id = models.CharField(max_length=255)
    accuracy = models.IntegerField()


class MasterAvailability(models.Model):
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    date = models.DateField()
    available_slots = models.JSONField()  # mavjud bo'lgan vaqt slotlari ro'yxati
    discount_percent = models.PositiveIntegerField(default=0)  # chegirma foizi

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('master', 'date')

    def __str__(self):
        return f"{self.master.full_name} - {self.date}"







class OTP(models.Model):
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resend_available_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class GuestProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guest_profile")

    telegram_id = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GuestProfile for {self.user.username}"
    

