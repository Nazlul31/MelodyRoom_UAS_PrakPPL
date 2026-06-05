from datetime import time

from .models import Booking, Room
from .constants import MIN_OPERATING_HOUR, MAX_OPERATING_HOUR

# Jam operasional: 17:00 - 02:00 (tengah malam ke hari berikutnya)
OPERATING_HOURS = list(range(17, 24))  # Display di jadwal: jam 17:00-23:00


def hour_to_time(hour):
    return time(hour, 0)


def get_bookings_for_date(booking_date):
    return Booking.objects.filter(
        booking_date=booking_date,
        status__in=[Booking.Status.PENDING, Booking.Status.LUNAS],
    ).select_related('room', 'user')


def build_schedule_grid(booking_date):
    """Dict { room: { hour: 'free' | 'pending' | 'lunas' } } untuk halaman jadwal."""
    bookings = get_bookings_for_date(booking_date)
    rooms = Room.objects.filter(is_active=True).order_by('room_code')
    grid = {}

    for room in rooms:
        grid[room] = {h: 'free' for h in OPERATING_HOURS}
        for booking in bookings.filter(room=room):
            status_key = 'lunas' if booking.status == Booking.Status.LUNAS else 'pending'
            for h in OPERATING_HOURS:
                slot_start = hour_to_time(h)
                slot_end = time(23, 59) if h == 23 else hour_to_time(h + 1)
                if booking.start_time < slot_end and booking.end_time > slot_start:
                    grid[room][h] = status_key

    return grid
