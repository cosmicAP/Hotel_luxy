from django.contrib import admin
from .models import Hotel, Room, Booking


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'rating', 'rate_per_night', 'created_at')
    search_fields = ('name', 'city', 'description')
    list_filter = ('rating', 'city')
    ordering = ('name',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'room_no', 'room_type', 'capacity', 'ac', 'price')
    list_filter = ('ac', 'room_type', 'hotel')
    search_fields = ('room_no', 'hotel__name', 'room_type')
    list_select_related = ('hotel',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'room', 'hotel_name', 'check_in_date', 'check_out_date', 'no_of_people', 'status', 'total_cost_display')
    search_fields = ('user_name', 'user_email', 'room__hotel__name')
    list_filter = ('status', 'check_in_date', 'check_out_date')
    list_select_related = ('room', 'room__hotel')

    @admin.display(description='Hotel')
    def hotel_name(self, obj):
        return obj.room.hotel.name

    @admin.display(description='Total Cost')
    def total_cost_display(self, obj):
        return f"₹{obj.total_cost}"