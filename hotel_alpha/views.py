from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
import json

from openai import OpenAI
from .models import Hotel, Room, Booking
from .forms import BookingForm

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome aboard.")
            return redirect('home_allo')
    else:
        form = UserCreationForm()
    return render(request, "auth/signup.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home_allo')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


def home(request):
    query = request.GET.get('q', '')
    city_filter = request.GET.get('city', '')
    sort = request.GET.get('sort', '-rating')

    hotels = Hotel.objects.all()

    if query:
        hotels = hotels.filter(Q(name__icontains=query) | Q(city__icontains=query) | Q(description__icontains=query))
    if city_filter:
        hotels = hotels.filter(city__icontains=city_filter)

    hotels = hotels.order_by(sort)

    cities = Hotel.objects.values_list('city', flat=True).distinct().order_by('city')

    paginator = Paginator(hotels, 9)
    page = request.GET.get('page', 1)
    try:
        hotels_page = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        hotels_page = paginator.page(1)

    context = {
        "hotels": hotels_page,
        "query": query,
        "city_filter": city_filter,
        "sort": sort,
        "cities": cities,
    }
    return render(request, "hotels/home.html", context)


@login_required
def hotel_rooms(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    rooms = hotel.rooms.all()
    context = {"hotel": hotel, "rooms": rooms}
    return render(request, "hotels/rooms.html", context)


@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        form = BookingForm(request.POST, room=room)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.room = room
            booking.user = request.user
            booking.save()

            try:
                send_mail(
                    subject='Booking Confirmation - Simple Hotel',
                    message=(
                        f"Hi {booking.user_name},\n\n"
                        f"Your booking for Room #{booking.room.room_no} ({booking.room.room_type}) "
                        f"at {booking.room.hotel.name} has been confirmed.\n\n"
                        f"Check-in: {booking.check_in_date}\n"
                        f"Check-out: {booking.check_out_date}\n"
                        f"Guests: {booking.no_of_people}\n"
                        f"Total: ₹{booking.total_cost}\n\n"
                        f"Thank you for choosing Simple Hotel!"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking.user_email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Warning: Failed to send email: {e}")

            messages.success(request, f"Room #{booking.room.room_no} booked successfully!")
            return redirect('bookings_dashboard')
    else:
        form = BookingForm(
            initial={
                'user_name': request.user.get_full_name() or request.user.username,
                'user_email': request.user.email,
            },
            room=room,
        )

    return render(request, "hotels/book_room.html", {"room": room, "form": form})


@login_required
def bookings_dashboard(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(user=request.user)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    bookings = bookings.order_by('-created_at')

    paginator = Paginator(bookings, 10)
    page = request.GET.get('page', 1)
    try:
        bookings_page = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        bookings_page = paginator.page(1)

    return render(request, "hotels/bookings.html", {
        "bookings": bookings_page,
        "status_filter": status_filter,
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status == 'CONFIRMED':
        booking.status = 'CANCELLED'
        booking.save()
        messages.warning(request, f"Booking cancelled for Room #{booking.room.room_no}.")
    else:
        messages.info(request, "This booking is already cancelled.")
    return redirect("bookings_dashboard")


@login_required
def profile_view(request):
    if request.method == "POST":
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
    return render(request, "auth/profile.html")


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "auth/change_password.html", {"form": form})


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    f"/password-reset/{uid}/{token}/"
                )
                send_mail(
                    subject='Password Reset - Simple Hotel',
                    message=f"Click the link below to reset your password:\n\n{reset_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
                messages.success(request, "Password reset link sent. Check your email.")
                return redirect('login')
            except User.DoesNotExist:
                messages.success(request, "If that email exists, a reset link has been sent.")
                return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, "auth/password_reset.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user=user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Password reset successful! You can now log in.")
                return redirect('login')
        else:
            form = SetPasswordForm(user=user)
        return render(request, "auth/password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "Invalid or expired reset link.")
        return redirect('password_reset')


client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://api.deepseek.com/v1"
)


@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        hotels = Hotel.objects.all()
        hotel_lines = []
        if hotels.exists():
            for h in hotels:
                hotel_lines.append(
                    f"- {h.name} ({h.city}) | {h.rating}★ | ₹{h.rate_per_night}/night | {h.description}"
                )
        else:
            hotel_lines.append("No hotels available.")

        system_prompt = (
            "You are a helpful hotel booking assistant for 'Simple Hotel.' "
            "You MUST answer using ONLY the hotel data below. "
            "If a user asks about a city not in the list, say we don't have hotels there. "
            "Be concise, friendly, and suggest alternatives when possible.\n\n"
            "AVAILABLE HOTELS:\n" + "\n".join(hotel_lines)
        )

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=300,
                temperature=0.7,
            )
            bot_reply = response.choices[0].message.content
            return JsonResponse({"reply": bot_reply})
        except Exception as e:
            return JsonResponse({"reply": "Sorry, I'm having trouble connecting to my brain right now. Please try again later."})

    return JsonResponse({"error": "Invalid request method"}, status=405)