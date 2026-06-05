from django.core.management.base import BaseCommand

from karaoke.models import Room


class Command(BaseCommand):
    help = 'Atur ulang posisi denah semua ruangan secara otomatis'

    def handle(self, *args, **options):
        rooms = Room.objects.order_by('room_code')
        for room in rooms:
            room.grid_row = 0
            room.grid_col = 0
            room.save()
        self.stdout.write(self.style.SUCCESS(f'{rooms.count()} ruangan diatur ulang di denah.'))
