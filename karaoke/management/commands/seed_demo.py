from decimal import Decimal

from django.core.management.base import BaseCommand

from karaoke.models import BookingPackage, Facility, Room, RoomType


class Command(BaseCommand):
    help = 'Isi data demo untuk pengujian MelodyRoom'

    def handle(self, *args, **options):
        packages = [
            ('Paket 1 Jam', 1, 'Sewa singkat & fleksibel'),
            ('Paket 2 Jam', 2, 'Paling populer untuk hangout'),
            ('Paket 3 Jam', 3, 'Sesi panjang, lebih hemat per jam'),
        ]
        for i, (name, hours, desc) in enumerate(packages):
            BookingPackage.objects.get_or_create(
                name=name,
                defaults={
                    'duration_hours': hours,
                    'description': desc,
                    'display_order': i,
                    'is_active': True,
                },
            )

        vip, _ = RoomType.objects.get_or_create(
            name='VIP Room',
            defaults={
                'capacity': 10,
                'price_per_hour': Decimal('150000'),
                'description': 'Ruangan premium dengan sound system terbaik dan interior mewah.',
                'is_active': True,
            },
        )
        standard, _ = RoomType.objects.get_or_create(
            name='Standard Room',
            defaults={
                'capacity': 6,
                'price_per_hour': Decimal('80000'),
                'description': 'Ruangan nyaman untuk grup kecil, cozy & intimate.',
                'is_active': True,
            },
        )

        rooms_data = [
            ('A01', 'VIP Aurora', vip, 10, Decimal('150000'), 1, 1),
            ('A02', 'VIP Nebula', vip, 10, Decimal('150000'), 1, 2),
            ('B01', 'Standard Breeze', standard, 6, Decimal('80000'), 2, 1),
            ('B02', 'Standard Echo', standard, 6, Decimal('80000'), 2, 2),
        ]
        for code, name, rtype, cap, price, row, col in rooms_data:
            Room.objects.get_or_create(
                room_code=code,
                defaults={
                    'room_type': rtype,
                    'name': name,
                    'capacity': cap,
                    'price_per_hour': price,
                    'description': f'Unit {code}',
                    'grid_row': row,
                    'grid_col': col,
                    'is_active': True,
                },
            )

        Facility.objects.get_or_create(
            name='Sound System Premium',
            defaults={'description': 'Speaker & mikrofon kelas studio', 'icon': '♪', 'display_order': 1},
        )
        Facility.objects.get_or_create(
            name='Private Lounge',
            defaults={'description': 'Interior elegan & lighting ambience', 'icon': '✦', 'display_order': 2},
        )
        Facility.objects.get_or_create(
            name='Snack & Beverage',
            defaults={'description': 'Menu minuman dan camilan pilihan', 'icon': '◈', 'display_order': 3},
        )

        self.stdout.write(self.style.SUCCESS('Data demo berhasil ditambahkan (termasuk paket sewa).'))
