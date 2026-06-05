from django.contrib import admin

from .models import Booking, BookingPackage, Facility, Room, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'price_per_hour', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_code', 'name', 'room_type', 'capacity', 'price_per_hour', 'is_active')
    list_filter = ('room_type', 'is_active')
    search_fields = ('room_code', 'name')


@admin.register(BookingPackage)
class BookingPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_hours', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'room', 'package', 'booking_date',
        'start_time', 'end_time', 'status', 'total_price',
    )
    list_filter = ('status', 'booking_date')
    search_fields = ('user__username', 'room__room_code')
    date_hierarchy = 'booking_date'


admin.site.register(Facility)
