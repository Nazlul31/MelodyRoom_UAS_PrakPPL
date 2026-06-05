from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('beranda/', views.user_beranda, name='beranda'),
    path('ruangan/', views.room_type_list, name='room_type_list'),
    path('ruangan/<int:pk>/', views.room_type_detail, name='room_type_detail'),
    path('jadwal/', views.schedule, name='schedule'),
    path('api/harga-paket/', views.package_price_api, name='package_price_api'),
    # Auth
    path('accounts/login/', views.MelodyLoginView.as_view(), name='login'),
    path('accounts/logout/', views.MelodyLogoutView.as_view(), name='logout'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    # Member
    path('pesan/', views.booking_create, name='booking_create'),
    path('pesanan-saya/', views.my_bookings, name='my_bookings'),
    # Custom admin dashboard
    path('dashboard-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard-admin/tipe-ruangan/', views.admin_room_type_list, name='admin_room_type_list'),
    path('dashboard-admin/tipe-ruangan/tambah/', views.admin_room_type_create, name='admin_room_type_create'),
    path('dashboard-admin/tipe-ruangan/<int:pk>/edit/', views.admin_room_type_edit, name='admin_room_type_edit'),
    path('dashboard-admin/ruangan/', views.admin_room_list, name='admin_room_list'),
    path('dashboard-admin/ruangan/tambah/', views.admin_room_create, name='admin_room_create'),
    path('dashboard-admin/ruangan/<int:pk>/edit/', views.admin_room_edit, name='admin_room_edit'),
    path('dashboard-admin/ruangan/<int:pk>/hapus/', views.admin_room_delete, name='admin_room_delete'),
    path('dashboard-admin/pesanan/', views.admin_booking_list, name='admin_booking_list'),
    path('dashboard-admin/denah/', views.admin_floor_plan, name='admin_floor_plan'),
    path(
        'dashboard-admin/pesanan/<int:pk>/lunas/',
        views.admin_booking_quick_lunas,
        name='admin_booking_quick_lunas',
    ),
]
