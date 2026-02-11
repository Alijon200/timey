from django.urls import path

from . import views



urlpatterns = [
    #Booking URLs
    path('booking/', views.BookingCreateView.as_view(), name='booking'),
    path('api/bookings/<int:id>/', views.BookingMasterActionView.as_view(), name='booking-master-action'),
    path('api/bookings/<int:id>/confirm', views.BookingClientConfirmAPIView.as_view(), name='booking-client-confirm'),
    path('api/bookings/<int:id>/complete', views.BookingCompleteAPIView.as_view(), name='booking-complete'),


    #Master URLs
    path('test/', views.TestAPIView.as_view(), name='test-api'),
    path('masters/', views.MasterCreateAPIView.as_view(), name='master-create'),
    path('masters/list/', views.MasterListAPIView.as_view(), name='master-list'),
    path('masters/<int:master_id>/availability/', views.MasterAvailabilityPatchAPIView.as_view(), name='master-availability-patch'),
    path('masters/<int:id>/', views.MasterDetailAPIView.as_view(), name='master-detail'),
    path('masters/<int:master_id>/next-available-time/', views.MasterNextAvailableTimeAPIView.as_view() , name='master-next-available-time'),

    #OTP URLs
    path("api/auth/master/send-otp", views.MasterSendOtpAPIView.as_view()),
    path("api/auth/master/verify-otp", views.MasterVerifyOtpAPIView.as_view()),


    #Telegram URLs
    path("api/auth/guest/create", views.GuestUserCreateAPIView.as_view(), name="guest-create"),
]