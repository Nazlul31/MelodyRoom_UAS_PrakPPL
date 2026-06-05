# 🎤 MelodyRoom

Sistem Informasi & Reservasi Penyewaan Ruang Karaoke berbasis web. Dibangun dengan Django, mendukung pemesanan online real-time, manajemen ruangan, dan denah interaktif untuk admin.

---

## Fitur Utama

### Untuk Member
- Registrasi & login akun
- Lihat daftar ruangan beserta tipe dan harga
- Cek jadwal ketersediaan ruangan per jam secara real-time
- Buat reservasi dengan pemilihan ruangan, paket durasi, tanggal, dan jam
- Preview harga otomatis saat memilih paket
- Riwayat pemesanan dengan status (Pending / Lunas / Batal)
- Dashboard member dengan info booking aktif

### Untuk Admin (Staff)
- Dashboard ringkasan statistik harian
- Kelola tipe ruangan (CRUD)
- Kelola unit ruangan fisik (CRUD)
- Kelola seluruh pesanan masuk dengan filter status
- Konfirmasi pembayaran (ubah status Pending → Lunas) satu klik
- **Denah interaktif real-time** — tampilan grid ruangan dengan warna status:
  - 🟢 Hijau = Tersedia
  - 🟡 Kuning = Pending (menunggu pembayaran)
  - 🔴 Merah = Terpakai (sedang berlangsung)
- Mendukung booking cross-midnight (jam operasional 17:00–02:00)

---

## Tech Stack

| Komponen | Detail |
|---|---|
| Backend | Django 6.0.6 |
| Database | SQLite |
| Frontend | Vanilla CSS (light mode), Plus Jakarta Sans |
| Image | Pillow 12.2.0 |
| Timezone | Asia/Jakarta |
| Python | 3.x |

---

## Struktur Proyek

```
MelodyRoom/
├── karaoke/                    # Aplikasi utama
│   ├── models.py               # RoomType, Room, BookingPackage, Booking, Facility
│   ├── views.py                # Semua view (publik, member, admin)
│   ├── urls.py                 # URL routing
│   ├── forms.py                # Form reservasi, registrasi, kelola ruangan
│   ├── utils.py                # Helper jadwal grid
│   ├── constants.py            # Jam operasional (17:00–02:00)
│   ├── context_processors.py   # Injeksi current_path ke template
│   ├── admin.py                # Django admin registration
│   ├── templates/karaoke/      # Semua template HTML
│   ├── templatetags/           # Custom template tag (karaoke_extras)
│   └── management/commands/    # Seed data & utility commands
├── melodyroom/                 # Konfigurasi proyek Django
│   └── settings.py
├── static/
│   ├── css/style.css
│   └── images/                 # Gambar statis lokal (about.jpg, dll)
├── media/                      # Upload foto ruangan
├── requirements.txt
└── manage.py
```

---

## Instalasi & Menjalankan Proyek

### 1. Clone / Download proyek

```bash
git clone <url-repo>
cd MelodyRoom
```

### 2. Buat virtual environment

```bash
python -m venv venv
```

### 3. Aktifkan virtual environment

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Jalankan migrasi database

```bash
python manage.py migrate
```

### 6. (Opsional) Seed data demo

```bash
# Seed paket sewa, tipe ruangan, unit ruangan, dan fasilitas
python manage.py seed_demo
```

### 7. Buat akun superuser (admin)

```bash
python manage.py createsuperuser
```

### 8. Jalankan server

```bash
python manage.py runserver
```

Akses di browser: **http://127.0.0.1:8000**

---

## URL Penting

| URL | Keterangan |
|---|---|
| `/` | Landing page |
| `/beranda/` | Dashboard member |
| `/ruangan/` | Daftar ruangan |
| `/jadwal/` | Jadwal ketersediaan |
| `/pesan/` | Form reservasi |
| `/pesanan-saya/` | Riwayat pesanan member |
| `/accounts/login/` | Login |
| `/accounts/register/` | Registrasi |
| `/dashboard-admin/` | Dashboard admin |
| `/dashboard-admin/denah/` | Denah interaktif |
| `/dashboard-admin/pesanan/` | Kelola pesanan |
| `/dashboard-admin/ruangan/` | Kelola unit ruangan |
| `/admin/` | Django admin panel |

---

## Management Commands

```bash
# Seed paket sewa default (1, 2, 3 jam)
python manage.py seed_packages

# Seed data demo lengkap (ruangan, tipe, fasilitas)
python manage.py seed_demo

# Reset seluruh data
python manage.py reset_data

# Reassign posisi grid denah ruangan
python manage.py reassign_grid
```

---

## Catatan

- Jam operasional: **17:00 – 02:00** (cross-midnight didukung)
- Booking yang melewati tengah malam ditangani secara otomatis di validasi form dan denah real-time
- Gambar ruangan bisa diupload melalui form admin; jika tidak ada, akan menggunakan gambar fallback
- Foto section About di landing page disimpan di `static/images/about.jpg`
