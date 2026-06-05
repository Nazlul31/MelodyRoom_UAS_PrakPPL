from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from .forms import BookingForm, BookingStatusForm, RegisterForm, RoomForm, RoomTypeForm
from .models import Booking, BookingPackage, Facility, Room, RoomType
from .utils import OPERATING_HOURS, build_schedule_grid


def staff_required(user):
    return user.is_authenticated and user.is_staff


# --- Landing (publik, tanpa daftar ruangan) ---

def landing(request):
    return render(
        request,
        'karaoke/landing.html',
        {'facilities': Facility.objects.filter(is_active=True)},
    )


@login_required
def user_beranda(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    
    # Ambil pemesanan terdekat yang aktif atau akan datang
    now = timezone.localtime()
    upcoming_bookings = request.user.bookings.filter(
        status__in=[Booking.Status.PENDING, Booking.Status.LUNAS],
        booking_date__gte=now.date()
    ).order_by('booking_date', 'start_time')
    
    active_booking = None
    for b in upcoming_bookings:
        if b.end_datetime > now:
            active_booking = b
            break
            
    return render(
        request,
        'karaoke/beranda.html',
        {
            'active_booking': active_booking,
        }
    )


def room_type_list(request):
    return render(
        request,
        'karaoke/room_type_list.html',
        {
            'rooms': Room.objects.filter(is_active=True).select_related('room_type'),
            'packages': BookingPackage.objects.filter(is_active=True),
        },
    )


def room_type_detail(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk, is_active=True)
    rooms = room_type.rooms.filter(is_active=True)
    packages = BookingPackage.objects.filter(is_active=True)
    return render(
        request,
        'karaoke/room_type_detail.html',
        {
            'room_type': room_type,
            'rooms': rooms,
            'packages': packages,
        },
    )


def schedule(request):
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            booking_date = date.fromisoformat(selected_date)
        except ValueError:
            booking_date = timezone.localdate()
    else:
        booking_date = timezone.localdate()

    grid = build_schedule_grid(booking_date)
    schedule_rows = [
        {
            'room': room,
            'slots': [(hour, grid[room][hour]) for hour in OPERATING_HOURS],
        }
        for room in grid
    ]
    return render(
        request,
        'karaoke/schedule.html',
        {
            'booking_date': booking_date,
            'schedule_rows': schedule_rows,
            'operating_hours': OPERATING_HOURS,
        },
    )


def package_price_api(request):
    """Hitung harga paket × ruangan (untuk preview di form)."""
    room_id = request.GET.get('room')
    package_id = request.GET.get('package')
    if not room_id or not package_id:
        return JsonResponse({'error': 'Parameter tidak lengkap'}, status=400)
    room = get_object_or_404(Room, pk=room_id, is_active=True)
    package = get_object_or_404(BookingPackage, pk=package_id, is_active=True)
    total = room.price_per_hour * package.duration_hours
    return JsonResponse({
        'total': int(total),
        'total_formatted': f'{int(total):,}'.replace(',', '.'),
        'duration_hours': package.duration_hours,
    })


# --- Autentikasi ---

class MelodyLoginView(LoginView):
    template_name = 'karaoke/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('beranda')


class MelodyLogoutView(LogoutView):
    next_page = reverse_lazy('landing')


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'karaoke/auth/register.html'
    success_url = reverse_lazy('beranda')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Akun berhasil dibuat. Selamat datang di MelodyRoom!')
        return response


# --- Member (bukan staff) ---

@login_required
def booking_create(request):
    if request.user.is_staff:
        messages.info(request, 'Kelola pesanan melalui Dashboard Admin.')
        return redirect('admin_booking_list')

    packages = BookingPackage.objects.filter(is_active=True)
    rooms = Room.objects.filter(is_active=True).select_related('room_type')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = Booking(
                user=request.user,
                room=form.cleaned_data['room'],
                package=form.cleaned_data['package'],
                booking_date=form.cleaned_data['booking_date'],
                start_time=form.cleaned_data['start_time'],
                end_time=form.cleaned_data['end_time'],
                notes=form.cleaned_data.get('notes', ''),
                status=Booking.Status.PENDING,
            )
            booking.save()
            messages.success(
                request,
                f'Pesanan berhasil! Paket {booking.package.name} — '
                f'Total Rp {booking.total_price:,.0f}. Menunggu konfirmasi pembayaran.',
            )
            return redirect('my_bookings')
    else:
        initial = {}
        room_id = request.GET.get('room')
        if room_id:
            initial['room'] = room_id
        form = BookingForm(initial=initial)

    return render(
        request,
        'karaoke/booking_form.html',
        {'form': form, 'packages': packages, 'rooms': rooms},
    )


@login_required
def my_bookings(request):
    if request.user.is_staff:
        return redirect('admin_booking_list')
    bookings = request.user.bookings.select_related(
        'room', 'room__room_type', 'package'
    )
    return render(request, 'karaoke/my_bookings.html', {'bookings': bookings})


# --- Custom Admin Dashboard (staff only) ---

@user_passes_test(staff_required, login_url='login')
def admin_dashboard(request):
    today = timezone.localdate()
    stats = {
        'total_rooms': Room.objects.filter(is_active=True).count(),
        'pending_today': Booking.objects.filter(
            booking_date=today, status=Booking.Status.PENDING
        ).count(),
        'active_now': Booking.objects.filter(
            status=Booking.Status.LUNAS,
            booking_date=today,
        ).count(),
        'total_bookings': Booking.objects.count(),
    }
    recent = Booking.objects.select_related('user', 'room', 'package')[:8]
    return render(
        request,
        'karaoke/admin/dashboard.html',
        {'stats': stats, 'recent_bookings': recent},
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_type_list(request):
    room_types = RoomType.objects.all()
    return render(
        request,
        'karaoke/admin/room_type_list.html',
        {'room_types': room_types},
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_type_create(request):
    if request.method == 'POST':
        form = RoomTypeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipe ruangan berhasil ditambahkan.')
            return redirect('admin_room_type_list')
    else:
        form = RoomTypeForm()
    return render(
        request,
        'karaoke/admin/room_type_form.html',
        {'form': form, 'title': 'Tambah Tipe Ruangan'},
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_type_edit(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk)
    if request.method == 'POST':
        form = RoomTypeForm(request.POST, request.FILES, instance=room_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipe ruangan berhasil diperbarui.')
            return redirect('admin_room_type_list')
    else:
        form = RoomTypeForm(instance=room_type)
    return render(
        request,
        'karaoke/admin/room_type_form.html',
        {'form': form, 'title': 'Edit Tipe Ruangan'},
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_list(request):
    rooms = Room.objects.select_related('room_type').all()
    return render(request, 'karaoke/admin/room_list.html', {'rooms': rooms})


@user_passes_test(staff_required, login_url='login')
def admin_room_create(request):
    if not RoomType.objects.filter(is_active=True).exists():
        messages.warning(
            request,
            'Anda harus membuat minimal satu Tipe Ruangan sebelum menambah unit ruangan.',
        )
        return redirect('admin_room_type_create')

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ruangan baru berhasil ditambahkan.')
            return redirect('admin_room_list')
    else:
        form = RoomForm()
    return render(
        request,
        'karaoke/admin/room_form.html',
        {
            'form': form,
            'title': 'Tambah Ruangan',
            'room_types_exist': True,
        },
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data ruangan berhasil diperbarui.')
            return redirect('admin_room_list')
    else:
        form = RoomForm(instance=room)
    return render(
        request,
        'karaoke/admin/room_form.html',
        {'form': form, 'title': 'Edit Ruangan', 'room': room},
    )


@user_passes_test(staff_required, login_url='login')
def admin_room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Ruangan berhasil dihapus.')
        return redirect('admin_room_list')
    return render(request, 'karaoke/admin/room_confirm_delete.html', {'room': room})


@user_passes_test(staff_required, login_url='login')
def admin_booking_list(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.select_related('user', 'room', 'package').all()
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        booking = get_object_or_404(Booking, pk=booking_id)
        form = BookingStatusForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, f'Status pesanan #{booking.id} diperbarui.')
            return redirect('admin_booking_list')

    return render(
        request,
        'karaoke/admin/booking_list.html',
        {
            'bookings': bookings,
            'status_filter': status_filter,
            'status_choices': Booking.Status.choices,
        },
    )


@user_passes_test(staff_required, login_url='login')
def admin_floor_plan(request):
    rooms = Room.objects.filter(is_active=True).select_related('room_type')
    room_data = []
    now = timezone.localtime()
    today = now.date()
    yesterday = today - timedelta(days=1)
    current_time = now.time()

    for room in rooms:
        # Cari booking LUNAS yang sedang aktif — handle cross-midnight
        # Kasus 1: booking normal hari ini (start <= now <= end, end > start)
        # Kasus 2: cross-midnight hari ini (start <= now, end < start → belum lewat tengah malam)
        # Kasus 3: cross-midnight dari kemarin (booking_date=kemarin, end > now)
        active = room.bookings.filter(
            status=Booking.Status.LUNAS,
            booking_date=today,
            start_time__lte=current_time,
            end_time__gt=current_time,
        ).first()

        if not active:
            # Cross-midnight: booking hari ini, end_time < start_time (lewat tengah malam)
            # dan sekarang belum tengah malam (masih di sisi start)
            active = room.bookings.filter(
                status=Booking.Status.LUNAS,
                booking_date=today,
                start_time__lte=current_time,
                end_time__lt=models.F('start_time'),  # cross-midnight
            ).first()

        if not active:
            # Cross-midnight dari kemarin: booking_date kemarin, end_time > now (sudah lewat tengah malam)
            active = room.bookings.filter(
                status=Booking.Status.LUNAS,
                booking_date=yesterday,
                end_time__gt=current_time,
                end_time__lt=models.F('start_time'),  # end < start = cross-midnight
            ).first()

        # Sama untuk PENDING
        pending = room.bookings.filter(
            status=Booking.Status.PENDING,
            booking_date=today,
            start_time__lte=current_time,
            end_time__gt=current_time,
        ).first()

        if not pending:
            pending = room.bookings.filter(
                status=Booking.Status.PENDING,
                booking_date=today,
                start_time__lte=current_time,
                end_time__lt=models.F('start_time'),
            ).first()

        if not pending:
            pending = room.bookings.filter(
                status=Booking.Status.PENDING,
                booking_date=yesterday,
                end_time__gt=current_time,
                end_time__lt=models.F('start_time'),
            ).first()

        remaining = None
        if active:
            rem = active.remaining_time()
            if rem:
                total_seconds = int(rem.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes = remainder // 60
                remaining = f'{hours}j {minutes}m'

        room_data.append(
            {
                'room': room,
                'occupied': active is not None,
                'active_booking': active,
                'pending_booking': pending,
                'remaining': remaining,
            }
        )

    return render(
        request,
        'karaoke/admin/floor_plan.html',
        {'room_data': room_data},
    )


@user_passes_test(staff_required, login_url='login')
def admin_booking_quick_lunas(request, pk):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        booking.status = Booking.Status.LUNAS
        booking.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Pesanan #{booking.id} ditandai LUNAS.')
    return redirect(request.POST.get('next', 'admin_floor_plan'))
