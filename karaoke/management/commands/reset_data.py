from django.core.management.base import BaseCommand
from django.db import transaction

from karaoke.models import Booking, Facility, Room, RoomType


class Command(BaseCommand):
    help = (
        'Hapus semua data ruangan, pesanan, dan fasilitas dummy. '
        'Paket sewa & akun user tetap ada. Gunakan sebelum input data asli admin.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Lewati konfirmasi',
        )

    def handle(self, *args, **options):
        if not options['yes']:
            confirm = input(
                'Hapus SEMUA Booking, Room, RoomType, dan Facility? (ketik ya): '
            )
            if confirm.strip().lower() != 'ya':
                self.stdout.write(self.style.WARNING('Dibatalkan.'))
                return

        with transaction.atomic():
            booking_count = Booking.objects.count()
            room_count = Room.objects.count()
            type_count = RoomType.objects.count()
            facility_count = Facility.objects.count()

            Booking.objects.all().delete()
            Room.objects.all().delete()
            RoomType.objects.all().delete()
            Facility.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Data dihapus: {booking_count} pesanan, {room_count} ruangan, '
                f'{type_count} tipe ruangan, {facility_count} fasilitas.'
            )
        )
        self.stdout.write(
            'Selanjutnya: login admin → Kelola Ruangan / Django Admin → '
            'tambah Tipe Ruangan & Ruangan asli.'
        )
