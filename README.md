# LOGIX - Smart Portable Analyzer System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

> **Sistem monitoring lingkungan otomatis untuk pemantauan kualitas air, udara, dan cuaca secara real-time dengan integrasi KLHK (Kementerian Lingkungan Hidup dan Kehutanan).**

## 📋 Deskripsi

LOGIX adalah sistem IoT berbasis Raspberry Pi yang dirancang untuk:
- Mengumpulkan data dari berbagai sensor lingkungan (kualitas air, udara, cuaca)
- Menyimpan data secara otomatis ke database MySQL
- Menampilkan data real-time melalui web dashboard interaktif
- Mengirim data ke sistem KLHK secara otomatis
- Export data dalam format CSV ke USB atau download
- Konfigurasi WiFi dan kontrol sistem melalui web interface

## 🎯 Target Pengguna

- **Instansi Pemerintah**: KLHK, Dinas Lingkungan Hidup, BMKG
- **Industri**: Pabrik, pengolahan air, pertambangan
- **Penelitian**: Universitas, lembaga riset lingkungan
- **Pemantauan**: Kualitas sungai, danau, udara perkotaan

## ✨ Fitur Utama

### 📊 Monitoring Real-time
- Dashboard web responsif dengan visualisasi grafik (Plotly.js)
- Update data otomatis setiap 30 detik
- Mendukung 24+ parameter lingkungan
- Wind rose diagram untuk data angin
- Peta lokasi sensor (Leaflet.js)

### 💾 Manajemen Data
- Penyimpanan otomatis ke MySQL (dual table: data & tmp)
- Backup database berkala
- Export data dengan filter rentang waktu
- Export ke USB drive atau download langsung
- Log cleanup otomatis (systemd timer)

### 🌐 Integrasi Eksternal
- **KLHK Integration**: Pengiriman data otomatis ke sistem KLHK
- **Retry Mechanism**: Automatic retry untuk data gagal kirim
- **JWT Authentication**: Secure API communication

### ⚙️ Kontrol Sistem
- Konfigurasi WiFi melalui web interface
- Restart/shutdown Raspberry Pi
- Status monitoring koneksi jaringan
- Multi-user authentication untuk konfigurasi

## 🔧 Sensor yang Didukung

### Kualitas Air (16 Sensor)
- **pH200**: pH meter
- **COD200X**: COD (Chemical Oxygen Demand)
- **TSS200X**: TSS (Total Suspended Solids)
- **Ammonia200**: Ammonia / NH3-N
- **H1601**: Multi-parameter water quality
- **CONTLYTE**: Conductivity sensor
- **DS502**: Dissolved Oxygen

### Kualitas Udara & Cuaca (9 Sensor)
- **AT500**: Weather station (suhu, kelembaban, tekanan)
- **RT200**: Rain gauge
- **MACE**: Air quality monitoring
- **SEM5096**: Environmental sensor
- **SPECTRO**: Spectrometer
- **ISCAN**: Air scanner
- **LTNC**: Lightning detector
- **XYMD02**: Meteorological station

_Catatan: Aktivasi sensor dikonfigurasi melalui file `.env`_

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐
│  Sensors (16+)  │
│  RS485/Modbus   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   main.py       │ ◄── Sensor Data Collection
│   (Backend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MySQL Database │
│  (Docker)       │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    ▼         ▼          ▼         ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│app.py  │ │log.py│ │backup  │ │KLHK API │
│Web API │ │Logger│ │Service │ │Sender   │
└───┬────┘ └──────┘ └────────┘ └─────────┘
    │
    ▼
┌─────────────────┐
│   Frontend      │
│  HTML/JS/CSS    │
│  Dashboard      │
└─────────────────┘
```

## 📁 Struktur Folder

```
logix/
├── backend/              # Backend Python modules
│   ├── app.py           # Flask web server & REST API
│   ├── main.py          # Main sensor data collector
│   ├── config.py        # Database configuration
│   ├── backup.py        # Database backup service
│   ├── log.py           # Web-based log viewer
│   ├── hasSend.py       # HAS Environmental data sender
│   ├── logsSend.py      # Network & sensor logging
│   ├── log_cleanup.py   # Automatic log cleanup
│   │
│   └── sensors/         # Individual sensor modules
│       ├── at500.py     # Weather station
│       ├── ph200.py     # pH sensor
│       ├── cod200x.py   # COD sensor
│       ├── ammonia200.py
│       ├── sem5096.py
│       └── ... (13 more sensor drivers)
│
├── frontend/            # Web dashboard
│   ├── index.html       # Main dashboard page
│   ├── css/
│   │   └── style.css    # Dashboard styling
│   ├── js/
│   │   └── script.js    # Dashboard logic (Plotly, Leaflet)
│   └── images/
│
├── klhk/                # KLHK integration
│   ├── send.py          # Send data to KLHK API
│   └── retry.py         # Retry failed transmissions
│
├── config/              # Configuration files
│   └── .env             # Environment variables (NOT in git)
│
├── database/            # Database state & backups
│   └── backup_state.json
│
├── log/                 # Application logs
│   ├── web.log
│   ├── sensor.log
│   └── klhk.log
│
├── install.sh           # Installation script
├── uninstall.sh         # Uninstallation script
├── requirements.txt     # Python dependencies
├── logix                # CLI command wrapper
└── *.service            # Systemd service files
```

## 🚀 Instalasi

### Prasyarat

- **Hardware**: Raspberry Pi 4 (recommended) atau 3B+
- **OS**: Raspberry Pi OS (Debian-based)
- **Network**: Koneksi internet untuk instalasi
- **Storage**: Minimal 8GB SD Card

### Dependensi Sistem

```bash
sudo apt update
sudo apt install -y python3 python3-pip docker.io docker-compose mariadb-client git
```

### Instalasi Otomatis

**⚠️ PENTING**: Konfigurasi file `.env` sebelum instalasi!

```bash
# 1. Clone atau copy project ke Raspberry Pi
cd /home/pi/logix

# 2. Edit konfigurasi
nano config/.env

# 3. Jalankan installer
sudo bash install.sh
```

Installer akan:
- ✅ Validasi dependensi sistem
- ✅ Membuat Python virtual environment
- ✅ Install dependencies Python (requirements.txt)
- ✅ Setup MySQL container (Docker)
- ✅ Inisialisasi database dan tabel
- ✅ Membuat systemd services (7 services)
- ✅ Setup log cleanup timer
- ✅ Membuat CLI command `logix`

### Manual Installation

<details>
<summary>Klik untuk melihat instalasi manual</summary>

```bash
# 1. Setup virtual environment
python3 -m venv /home/pi/logix/venv
source /home/pi/logix/venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup MySQL (Docker)
docker run -d --name db_logix \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=logix \
  mysql:8.0

# 4. Initialize database
# (Run SQL schema - lihat install.sh untuk detail)

# 5. Create systemd services
# (Copy service files - lihat install.sh)

# 6. Start services
sudo systemctl start logix-sensor
sudo systemctl start logix-web
```

</details>

## 📝 Konfigurasi

### File: `config/.env`

```bash
# === Database Configuration ===
DB_HOST=localhost
DB_NAME=logix
DB_USER=root
DB_PASSWORD=your_secure_password
DB_PORT=3306

# === Application Ports ===
PORT_NUMBER_APP=5010    # Web dashboard port
PORT_NUMBER_LOG=5011    # Log viewer port

# === System Configuration ===
DEVICE_ID=LOGIX-001
LOCATION_NAME="Monitoring Station Alpha"
SOFTWARE_VERSION=1.0.0
TIMEZONE=Asia/Jakarta
DELAY=60                # Sensor reading interval (seconds)

# === Dashboard Configuration ===
WEB_TITLE="LOGIX Dashboard"
WEB_NAME="Smart Portable Analyzer"
GAP_WEB=6               # Chart gap threshold (minutes)

# === Geographic Location ===
GEO_LATITUDE=-6.200000
GEO_LONGITUDE=106.816666

# === Sensor Selection ===
# Parameter yang akan ditampilkan (comma-separated)
PARAMETERS=pH,orp,tds,conduct,do,salinity,nh3n,turb,tss,cod,bod,no3,atemp,wtemp,apress,wpress,battery,depth,flow,tflow,hum,wspeed,wdir,rain,srad

# === Sensor Status (active/inactive) ===
AT500_STATUS=active
PH200_STATUS=active
COD200X_STATUS=inactive
# ... (lihat .env.example untuk semua sensor)

# === KLHK Integration ===
KLHK_STATUS=active
KLHK_URL=https://api.klhk.go.id/v1
KLHK_TOKEN=your_jwt_token
# ... (konfigurasi KLHK lainnya)

# === Unit Configuration ===
SATUAN_PH=pH
SATUAN_ORP=mV
SATUAN_TDS=ppm
# ... (unit untuk semua parameter)
```

## 🎮 Penggunaan

### CLI Command

```bash
# Check status semua services
logix status

# Start/stop services
logix start
logix stop
logix restart

# View logs
logix logs sensor
logix logs web
logix logs klhk

# Help
logix help
```

### Web Dashboard

Akses dashboard di browser:

```
http://raspberry-pi-ip:5010
```

**Default Login** (untuk halaman konfigurasi):
- Username: `admin`
- Password: `has123456`


### API Endpoints

#### Public Endpoints
```bash
# Get latest sensor data
GET /api/latest

# Get historical data
GET /api/history?param=pH&range=1h

# Get wind rose data
GET /api/windrose?range=1d

# Get system config
GET /api/config

# Export data
POST /api/export
Body: {"start": "2024-01-01T00:00", "end": "2024-01-31T23:59", "destination": "download"}
```

#### Protected Endpoints (Require Login)
```bash
# Read configuration
GET /api/config/read

# Update configuration
POST /api/config/write

# System control
POST /api/system/restart
POST /api/system/shutdown
```

## 🛠️ Services

Sistem menggunakan 7 systemd services:

| Service | Deskripsi | Script |
|---------|-----------|--------|
| `logix-sensor` | Sensor data collection | `backend/main.py` |
| `logix-web` | Web dashboard & API | `backend/app.py` |
| `logix-web-log` | Log viewer web | `backend/log.py` |
| `logix-backup` | Database backup | `backend/backup.py` |
| `logix-klhk-send` | KLHK data transmission | `klhk/send.py` |
| `logix-klhk-retry` | KLHK retry mechanism | `klhk/retry.py` |
| `logix-has-send` | HAS data transmission | `backend/hasSend.py` |

### Service Management

```bash
# Check status
sudo systemctl status logix-sensor

# View logs
sudo journalctl -u logix-sensor -f

# Restart service
sudo systemctl restart logix-web

# Enable on boot
sudo systemctl enable logix-sensor
```

## 📊 Database Schema

### Table: `data`
Tabel utama untuk data berhasil dikirim

### Table: `tmp`
Tabel temporary untuk data proses kirim

### Columns
```sql
- id (PRIMARY KEY)
- date (DATETIME)
- device (VARCHAR)
- pH, orp, tds, conduct, do, salinity, nh3n (FLOAT)
- turb, tss, cod, bod, no3 (FLOAT)
- atemp, wtemp, apress, wpress (FLOAT)
- battery, depth, flow, tflow (FLOAT)
- hum, wspeed, wdir, rain, srad (FLOAT)
```

_Catatan: Kolom aktual disesuaikan dengan PARAMETERS yang dikonfigurasi_

## 🔒 Keamanan

- ✅ Session-based authentication untuk konfigurasi
- ✅ SHA256 password hashing
- ✅ Secure session cookies (HttpOnly, SameSite)
- ✅ Environment-based secrets (`.env`)
- ✅ JWT untuk KLHK API authentication
- ⚠️ Port filtering via firewall (recommended)
- ⚠️ Ubah default credentials setelah instalasi

## 🐛 Troubleshooting

### Service tidak berjalan

```bash
# Check service status
sudo systemctl status logix-sensor

# View detailed logs
sudo journalctl -u logix-sensor -n 50

# Restart service
sudo systemctl restart logix-sensor
```

### Database connection error

```bash
# Check MySQL container
docker ps | grep db_logix

# Check MySQL logs
docker logs db_logix

# Restart MySQL
docker restart db_logix
```

### Sensor tidak terbaca

```bash
# Check sensor configuration in .env
cat config/.env | grep STATUS

# Check sensor connection (RS485/Modbus)
# Verify port permissions
ls -l /dev/ttyUSB* /dev/ttyAMA*

# Add user to dialout group
sudo usermod -a -G dialout pi
```

### Web dashboard tidak muncul

```bash
# Check Flask service
sudo systemctl status logix-web

# Check port
sudo netstat -tlnp | grep 5010

# Check firewall
sudo ufw status
```

## 📦 Dependencies

### Python Packages
- **Flask 2.3.3**: Web framework
- **Polars 0.20.31**: Fast DataFrame library (replaces pandas)
- **mysql-connector-python**: MySQL database driver
- **python-dotenv**: Environment configuration
- **PyJWT**: JWT token handling
- **pyserial**: Serial communication
- **requests**: HTTP client
- **pytz**: Timezone handling

### Frontend Libraries (CDN)
- **Plotly.js**: Interactive charts
- **Leaflet.js**: Map visualization
- **Bootstrap 5.3.3**: UI framework
- **Flatpickr**: DateTime picker

## 🔄 Uninstall

```bash
sudo bash uninstall.sh
```

Akan menghapus:
- ✅ Semua systemd services
- ✅ Virtual environment
- ✅ MySQL Docker container
- ✅ Log cleanup timer
- ⚠️ Database data (backup dulu jika perlu!)

## 📞 Kontak & Support

**Developer**: Abu Bakar  
**Email**: abubakar.it.dev@gmail.com  
**Organization**: HAS Environmental

## 📄 Lisensi

Private/Internal Project - All Rights Reserved

---

**⚠️ CATATAN PENTING**:
1. File `.env` tidak di-commit ke git (ada di .gitignore)
2. Selalu backup database sebelum update
3. Test konfigurasi sensor secara bertahap
4. Monitor log secara berkala untuk deteksi error
5. Update password default setelah instalasi

**Last Updated**: 2025  
**Version**: 1.0.0
