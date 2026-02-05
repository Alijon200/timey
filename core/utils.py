from django.utils import timezone
from core.models import Booking, BookingStatus
from datetime import date
from .models import MasterAvailability



import math




def cancel_expired_bookings():
    now = timezone.now()

    Booking.objects.filter(
        status=BookingStatus.PENDING,
        expires_at__lt=now
    ).update(status=BookingStatus.CANCELLED)

    



def calculate_distance_km(lat1, lng1, lat2, lng2):
    R = 6371 
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


# today uchun bookinglarni qaytaradi
def get_today_bookings_for_master(master_id, date):
    return Booking.objects.filter(
        master_id=master_id,
        date=date,
        status__in=[
            BookingStatus.PENDING,
            BookingStatus.ACCEPTED,
            BookingStatus.CONFIRMED
        ]
    ).values_list('time', flat=True)


# master va date boyicha bo'sh slotlarni qaytaradi
def get_free_slots(master, date):
    availability = MasterAvailability.objects.filter(
        master=master,
        date=date
    ).first()

    if not availability:
        return []

    schedule_slots = availability.available_slots
    booked_slots = get_today_bookings_for_master(master.id, date)

    return [
        slot for slot in schedule_slots
        if slot not in booked_slots
    ]

# master va date boyicha availability ni qaytaradi
def get_master_availability(master, date=None):
    if not date:
        date = timezone.localdate()

    free_slots = get_free_slots(master, date)

    if not free_slots:
        return {
            "is_available_today": False,
            "next_available_time": None,
            "discount_percent": 0
        }

    availability = MasterAvailability.objects.filter(
        master=master,
        date=date
    ).first()

    return {
        "is_available_today": True,
        "next_available_time": free_slots[0],
        "discount_percent": availability.discount_percent if availability else 0
    }



#  today uchun availability ni qaytaradi
def get_today_availability(master):
    today = date.today()

    availability = MasterAvailability.objects.filter(
        master=master,
        date=today
    ).first()

    if not availability:
        return {
            "is_available_today": False,
            "next_available_time": None,
            "discount_percent": 0
        }

    slots = availability.available_slots.copy()

    bookings = Booking.objects.filter(
        master_id=master.id,
        date=today
    ).exclude(
        status=BookingStatus.CANCELLED
    )

    booked_times = [b.time.strftime("%H:%M") for b in bookings]

    free_slots = [s for s in slots if s not in booked_times]

    if not free_slots:
        return {
            "is_available_today": False,
            "next_available_time": None,
            "discount_percent": 0
        }

    return {
        "is_available_today": True,
        "next_available_time": free_slots[0],
        "discount_percent": availability.discount_percent
    }


def get_next_available_time(master):
    today = date.today()
    availability = master.availabilities.filter(date=today).first()
    if not availability:
        return None
    
    available_slots = availability.available_slots or []

    booked_slots = Booking.objects.filter(
        master_id=master.id,
        date=today,
        status=BookingStatus.CONFIRMED
        ).values_list('time', flat=True)
    
    free_slots = [
        slot for slot in available_slots if slot not in booked_slots
        ]
    
    return min(free_slots) if free_slots else None
