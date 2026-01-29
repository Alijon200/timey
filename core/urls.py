from django.urls import path

from . import views



urlpatterns = [
    #Booking URLs
    path('booking/', views.BookingCreateView.as_view(), name='booking'),
    path('api/bookings/<int:id>/', views.BookingMasterActionView.as_view(), name='booking-master-action'),
    path('api/bookings/<int:id>/confirm', views.BookingClientConfirmAPIView.as_view(), name='booking-client-confirm'),
    path('api/bookings/<int:id>/complete', views.BookingCompleteAPIView.as_view(), name='booking-complete'),


    #Master URLs
    path('masters/', views.MasterCreateAPIView.as_view()),
    path('masters/list/', views.MasterListAPIView.as_view()),
    path('masters/<int:master_id>/availability/', views.MasterAvailabilityUpdateAPIView.as_view()),

]