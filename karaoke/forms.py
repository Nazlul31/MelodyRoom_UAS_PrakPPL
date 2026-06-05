from datetime import datetime, timedelta, time

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Booking, BookingPackage, Room, RoomType
from .constants import MIN_OPERATING_HOUR, MAX_OPERATING_HOUR


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'email', 'password1', 'password2'):
            self.fields[name].widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class BookingForm(forms.Form):
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        label='Pilih Ruangan',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_room'}),
    )
    package = forms.ModelChoiceField(
        queryset=BookingPackage.objects.filter(is_active=True),
        label='Pilih Paket',
        widget=forms.RadioSelect(attrs={'class': 'package-radio'}),
    )
    booking_date = forms.DateField(
        label='Tanggal Main',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    start_time = forms.TimeField(
        label='Jam Mulai',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'id_start_time'}),
    )
    notes = forms.CharField(
        required=False,
        label='Catatan',
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Catatan opsional...'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(is_active=True).select_related('room_type')
        self.fields['package'].queryset = BookingPackage.objects.filter(is_active=True)
        self.fields['package'].label_from_instance = (
            lambda p: f'{p.name} ({p.duration_hours} jam)'
        )

    def clean(self):
        cleaned = super().clean()
        room = cleaned.get('room')
        package = cleaned.get('package')
        booking_date = cleaned.get('booking_date')
        start_time = cleaned.get('start_time')

        if not all([room, package, booking_date, start_time]):
            return cleaned

        # Validasi jam operasional: 17:00 - 02:00
        min_time = time(MIN_OPERATING_HOUR, 0)  # 17:00
        max_time = time(MAX_OPERATING_HOUR, 0)  # 02:00
        
        if start_time < min_time:
            raise ValidationError(f'Jam mulai harus {MIN_OPERATING_HOUR}:00 atau lebih.')
        
        end_time = Booking.compute_end_time(booking_date, start_time, package)
        cleaned['end_time'] = end_time
        
        # Untuk cross-midnight booking, end_time <= start_time
        # Validasi: end_time tidak boleh > 02:00 untuk next day
        if end_time <= start_time and end_time > max_time:
            # Cross-midnight yang melebihi jam tutup
            raise ValidationError(f'Booking dapat ditutup sampai {MAX_OPERATING_HOUR}:00 (hari berikutnya).')

        booking = Booking(
            room=room,
            package=package,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
        try:
            booking.clean()
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc

        return cleaned


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = (
            'name',
            'room_code',
            'capacity',
            'price_per_hour',
            'description',
            'photo',
            'is_active',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = (
                    'w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 '
                    'text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-2 '
                    'focus:ring-indigo-500/20 outline-none transition'
                )


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ('name', 'capacity', 'price_per_hour', 'description', 'photo', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget_class = (
            'w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 '
            'text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-2 '
            'focus:ring-indigo-500/20 outline-none transition'
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', widget_class)


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('status',)
