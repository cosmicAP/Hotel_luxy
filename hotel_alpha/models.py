from django.db import models
from django.utils import timezone

RATING_CHOICES = [
    (1, '1 Star'),
    (2, '2 Star'),
    (3, '3 Star'),
    (4, '4 Star'),
    (5, '5 Star'),
]

BOOKING_STATUS = [
    ('CONFIRMED', 'Confirmed'),
    ('CANCELLED', 'Cancelled'),
    ('COMPLETED', 'Completed'),
]


class Hotel(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='hotels/', null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, default=3)
    rate_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} | {self.city}"

    class Meta:
        ordering = ['-rating', 'name']


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=200)
    capacity = models.IntegerField(default=1)
    ac = models.BooleanField(default=True)
    room_no = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    amenities = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Room {self.room_no} | {self.room_type}"

    class Meta:
        unique_together = ['hotel', 'room_no']


class Booking(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    user_name = models.CharField(max_length=400)
    user_email = models.EmailField()
    user_phone_no = models.CharField(max_length=15)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    no_of_people = models.IntegerField(default=1)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='CONFIRMED')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    @property
    def total_cost(self):
        if self.check_in_date and self.check_out_date:
            days = (self.check_out_date - self.check_in_date).days
            if days <= 0:
                days = 1
            rate = self.room.price or self.room.hotel.rate_per_night
            return days * rate
        return 0

    @property
    def is_active(self):
        return self.status == 'CONFIRMED'

    def __str__(self):
        return f"Booking {self.id} | {self.user_name}"



    


