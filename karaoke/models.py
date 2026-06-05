from datetime import datetime, timedelta, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .constants import MIN_OPERATING_HOUR, MAX_OPERATING_HOUR


class RoomType(models.Model):
    """Kategori/tipe ruangan yang ditampilkan di halaman publik."""

    name = models.CharField(max_length=100, verbose_name='Nama Tipe')
    capacity = models.PositiveIntegerField(verbose_name='Kapasitas (orang)')
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Harga per Jam (Rp)',
    )
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    photo = models.ImageField(
        upload_to='room_types/',
        blank=True,
        null=True,
        verbose_name='Foto Ruangan',
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tipe Ruangan'
        verbose_name_plural = 'Tipe Ruangan'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.capacity} orang)'


class Room(models.Model):
    """Unit ruangan fisik untuk reservasi dan denah interaktif admin."""

    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rooms',
        verbose_name='Tipe Ruangan',
    )
    name = models.CharField(max_length=100, verbose_name='Nama Ruangan')
    room_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Kode Ruangan',
        help_text='Contoh: A01, VIP-1 (untuk denah grid)',
    )
    capacity = models.PositiveIntegerField(
        verbose_name='Kapasitas',
        help_text='Kosongkan logika UI bisa mengikuti tipe; isi jika berbeda dari tipe.',
    )
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Harga per Jam (Rp)',
        help_text='Bisa disamakan dengan tipe atau di-override per ruangan.',
    )
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    photo = models.ImageField(
        upload_to='rooms/',
        blank=True,
        null=True,
        verbose_name='Foto Ruangan',
    )
    grid_row = models.PositiveSmallIntegerField(default=0, editable=False)
    grid_col = models.PositiveSmallIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ruangan'
        verbose_name_plural = 'Ruangan'
        ordering = ['room_code']

    def __str__(self):
        return f'{self.room_code} - {self.name}'

    GRID_COLUMNS = 4

    def assign_grid_position(self):
        """Letakkan ruangan pada slot grid pertama yang kosong."""
        occupied = set(
            Room.objects.exclude(pk=self.pk)
            .filter(grid_row__gt=0, grid_col__gt=0)
            .values_list('grid_row', 'grid_col')
        )
        for row in range(1, 50):
            for col in range(1, self.GRID_COLUMNS + 1):
                if (row, col) not in occupied:
                    self.grid_row = row
                    self.grid_col = col
                    return

    def save(self, *args, **kwargs):
        if not self.grid_row or not self.grid_col:
            self.assign_grid_position()
        else:
            clash = (
                Room.objects.filter(grid_row=self.grid_row, grid_col=self.grid_col)
                .exclude(pk=self.pk)
                .exists()
            )
            if clash:
                self.assign_grid_position()
        super().save(*args, **kwargs)

    def is_occupied_now(self):
        """True jika ada booking LUNAS yang sedang berjalan pada waktu sekarang."""
        now = timezone.localtime()
        return self.bookings.filter(
            status=Booking.Status.LUNAS,
            booking_date=now.date(),
            start_time__lte=now.time(),
            end_time__gt=now.time(),
        ).exists()

    def active_booking_now(self):
        """Booking LUNAS yang sedang berjalan (untuk sisa waktu di denah)."""
        now = timezone.localtime()
        return self.bookings.filter(
            status=Booking.Status.LUNAS,
            booking_date=now.date(),
            start_time__lte=now.time(),
            end_time__gt=now.time(),
        ).first()


class BookingPackage(models.Model):
    """Paket durasi sewa dengan harga = harga/jam ruangan × durasi."""

    name = models.CharField(max_length=80, verbose_name='Nama Paket')
    duration_hours = models.PositiveSmallIntegerField(verbose_name='Durasi (jam)')
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Paket Sewa'
        verbose_name_plural = 'Paket Sewa'
        ordering = ['display_order', 'duration_hours']

    def __str__(self):
        return f'{self.name} ({self.duration_hours} jam)'


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Menunggu Pembayaran'
        LUNAS = 'LUNAS', 'Lunas'
        BATAL = 'BATAL', 'Dibatalkan'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Member',
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Ruangan',
    )
    package = models.ForeignKey(
        BookingPackage,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Paket',
    )
    booking_date = models.DateField(verbose_name='Tanggal Main')
    start_time = models.TimeField(verbose_name='Jam Mulai')
    end_time = models.TimeField(verbose_name='Jam Selesai')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status Pesanan',
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='Total Harga (Rp)',
    )
    notes = models.TextField(blank=True, verbose_name='Catatan')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pesanan'
        verbose_name_plural = 'Pesanan'
        ordering = ['-booking_date', '-start_time']
        indexes = [
            models.Index(fields=['booking_date', 'room']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return (
            f'{self.user.username} - {self.room.room_code} '
            f'({self.booking_date} {self.start_time}-{self.end_time})'
        )

    @property
    def duration_hours(self):
        if self.package_id:
            return Decimal(self.package.duration_hours)
        start = datetime.combine(self.booking_date, self.start_time)
        end = datetime.combine(self.booking_date, self.end_time)
        if end <= start:
            end += timedelta(days=1)
        delta = end - start
        return Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.01'))

    def calculate_total_price(self):
        return (self.duration_hours * self.room.price_per_hour).quantize(Decimal('1'))

    @staticmethod
    def compute_end_time(booking_date, start_time, package):
        start_dt = datetime.combine(booking_date, start_time)
        end_dt = start_dt + timedelta(hours=package.duration_hours)
        return end_dt.time()

    def is_active_now(self):
        """Pesanan LUNAS yang sedang berjalan pada waktu ini."""
        if self.status != self.Status.LUNAS:
            return False
        now = timezone.localtime()
        if self.booking_date != now.date():
            return False
        return self.start_time <= now.time() < self.end_time

    def remaining_time(self):
        """Sisa waktu sewa (untuk denah admin); None jika tidak sedang aktif."""
        if not self.is_active_now():
            return None
        now = timezone.localtime()
        end = datetime.combine(self.booking_date, self.end_time)
        if timezone.is_aware(now):
            end = timezone.make_aware(end, timezone.get_current_timezone())
        remaining = end - now.replace(tzinfo=end.tzinfo if timezone.is_aware(end) else None)
        return remaining

    @property
    def start_datetime(self):
        if not (self.booking_date and self.start_time):
            return None
        dt = datetime.combine(self.booking_date, self.start_time)
        if timezone.is_aware(timezone.now()):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    @property
    def end_datetime(self):
        if not (self.booking_date and self.end_time):
            return None
        dt = datetime.combine(self.booking_date, self.end_time)
        if self.end_time <= self.start_time:
            dt += timedelta(days=1)
        if timezone.is_aware(timezone.now()):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def clean(self):
        if self.booking_date and self.start_time and self.end_time:
            # Validasi jam operasional: 17:00 - 02:00
            min_time = time(MIN_OPERATING_HOUR, 0)  # 17:00
            max_time = time(MAX_OPERATING_HOUR, 0)  # 02:00
            
            if self.start_time < min_time:
                raise ValidationError('Jam mulai harus 17:00 atau lebih (jam operasional).')
            
            # Cross-midnight: end_time <= start_time, validasi end_time <= 02:00
            if self.end_time <= self.start_time and self.end_time > max_time:
                raise ValidationError('Booking dapat ditutup sampai 02:00 (hari berikutnya).')
            
            start_dt = self.start_datetime
            end_dt = self.end_datetime
            if end_dt <= start_dt:
                raise ValidationError('Jam selesai harus lebih besar dari jam mulai.')

            # Pemeriksaan pesanan bertabrakan (overlapping)
            # Karena booking bisa melewati tengah malam, kita periksa hari kemarin, hari ini, dan besok
            overlapping = Booking.objects.filter(
                room=self.room,
                booking_date__in=[
                    self.booking_date - timedelta(days=1),
                    self.booking_date,
                    self.booking_date + timedelta(days=1)
                ],
                status__in=[self.Status.PENDING, self.Status.LUNAS],
            ).exclude(pk=self.pk)

            for other in overlapping:
                other_start = other.start_datetime
                other_end = other.end_datetime
                # Jika rentang waktu bertabrakan
                if start_dt < other_end and end_dt > other_start:
                    raise ValidationError(
                        f'Ruangan {self.room.room_code} sudah dipesan pada jam tersebut.'
                    )

    def save(self, *args, **kwargs):
        if self.package_id and self.booking_date and self.start_time:
            self.end_time = self.compute_end_time(
                self.booking_date, self.start_time, self.package
            )
        self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)


class Facility(models.Model):
    """Fasilitas bisnis untuk landing page."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='Kelas ikon CSS atau emoji, misal: 🎤',
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Fasilitas'
        verbose_name_plural = 'Fasilitas'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
