from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home_allo"),
    path("hotel/<int:hotel_id>/rooms/", views.hotel_rooms, name="hotel_rooms"),
    path("room/<int:room_id>/book/", views.book_room, name="book_room"),
    path("bookings/", views.bookings_dashboard, name="bookings_dashboard"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("profile/", views.profile_view, name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("password-reset/", views.password_reset_request, name="password_reset"),
    path("password-reset/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
]

