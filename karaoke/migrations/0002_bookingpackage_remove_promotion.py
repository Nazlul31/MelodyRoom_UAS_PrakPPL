import django.db.models.deletion
from django.db import migrations, models


def create_packages_and_assign(apps, schema_editor):
    BookingPackage = apps.get_model('karaoke', 'BookingPackage')
    Booking = apps.get_model('karaoke', 'Booking')

    pkg1, _ = BookingPackage.objects.get_or_create(
        name='Paket 1 Jam',
        defaults={'duration_hours': 1, 'description': 'Default', 'display_order': 0, 'is_active': True},
    )
    BookingPackage.objects.get_or_create(
        name='Paket 2 Jam',
        defaults={'duration_hours': 2, 'description': '', 'display_order': 1, 'is_active': True},
    )
    BookingPackage.objects.get_or_create(
        name='Paket 3 Jam',
        defaults={'duration_hours': 3, 'description': '', 'display_order': 2, 'is_active': True},
    )

    for booking in Booking.objects.filter(package__isnull=True):
        booking.package = pkg1
        booking.save(update_fields=['package'])


class Migration(migrations.Migration):

    dependencies = [
        ('karaoke', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='Nama Paket')),
                ('duration_hours', models.PositiveSmallIntegerField(verbose_name='Durasi (jam)')),
                ('description', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Paket Sewa',
                'verbose_name_plural': 'Paket Sewa',
                'ordering': ['display_order', 'duration_hours'],
            },
        ),
        migrations.DeleteModel(
            name='Promotion',
        ),
        migrations.AddField(
            model_name='booking',
            name='package',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bookings',
                to='karaoke.bookingpackage',
                verbose_name='Paket',
            ),
        ),
        migrations.RunPython(create_packages_and_assign, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='booking',
            name='package',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bookings',
                to='karaoke.bookingpackage',
                verbose_name='Paket',
            ),
        ),
    ]
