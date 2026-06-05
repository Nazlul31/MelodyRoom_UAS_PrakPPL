from django.core.management.base import BaseCommand

from karaoke.models import BookingPackage


class Command(BaseCommand):
    help = 'Isi paket sewa default (1, 2, 3 jam) jika belum ada'

    def handle(self, *args, **options):
        packages = [
            ('Paket 1 Jam', 1, 'Sewa singkat'),
            ('Paket 2 Jam', 2, 'Populer untuk hangout'),
            ('Paket 3 Jam', 3, 'Sesi lebih panjang'),
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
        self.stdout.write(self.style.SUCCESS('Paket sewa siap digunakan.'))
