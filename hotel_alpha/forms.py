from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Booking, Room

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['user_name', 'user_email', 'user_phone_no', 'no_of_people', 'check_in_date', 'check_out_date']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)

    def clean_check_in_date(self):
        check_in = self.cleaned_data.get('check_in_date')
        if check_in and check_in < timezone.now().date():
            raise ValidationError("Check-in date cannot be in the past.")
        return check_in

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in_date')
        check_out = cleaned.get('check_out_date')
        no_of_people = cleaned.get('no_of_people')

        if check_in and check_out and check_in >= check_out:
            raise ValidationError("Check-out date must be after the check-in date.")

        if self.room and no_of_people and no_of_people > self.room.capacity:
            raise ValidationError(f"This room only accommodates {self.room.capacity} guest(s).")

        if check_in and check_out and self.room:
            overlapping = Booking.objects.filter(
                room=self.room,
                status='CONFIRMED',
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            )
            if overlapping.exists():
                raise ValidationError("This room is already booked for the selected dates. Please choose different dates.")

        return cleaned