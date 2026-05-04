# Logix - Smart Portable Analyzer System

**Sistem Pemantauan Lingkungan Otomatis Berbasis Web**

Aplikasi full-stack untuk pengumpulan data lingkungan real-time (cuaca dan kualitas air) melalui berbagai sensor terpadu, dengan dashboard web interaktif dan integrasi sistem pelaporan lingkungan (KLHK).

---

## 📋 Daftar Isi

- [Informasi Umum](#informasi-umum)
- [Fitur Utama](#fitur-utama)
- [Persyaratan Sistem](#persyaratan-sistem)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Penggunaan](#penggunaan)
- [Struktur Folder](#struktur-folder)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Sensors Didukung](#sensors-didukung)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Informasi Umum

| Informasi | Keterangan |
|-----------|-----------|
| **Nama Project** | Logix (Smart Portable Analyzer System) |
| **Tujuan** | Pemantauan otomatis data lingkungan (cuaca & kualitas air) |
| **Target User** | Teknisi/Operator pemantauan lingkungan, Administrator sistem |
| **Jenis Project** | Web Application (Full-Stack: Backend Python + Frontend HTML/CSS/JS) |
| **Framework Backend** | Flask (Python 3) |
| **Database** | MySQL (data sensor) + SQLite (konfigurasi) |
| **Lisensi** | Private/Internal Project |

---

## ✨ Fitur Utama

### Backend (Sensor & Data Collection)
- ✅ **Multi-Sensor Integration**: Dukungan 17+ jenis sensor dengan protokol Modbus TCP & Serial RS485
- ✅ **Scheduled Data Collection**: Pengumpulan data berkala yang dapat dikonfigurasi (interval 1-60 menit)
- ✅ **Database Storage**: Penyimpanan data ke MySQL dengan timestamp otomatis
- ✅ **Configuration Management**: SQLite untuk manajemen konfigurasi dinamis tanpa restart

### Frontend (Web Dashboard)
- ✅ **Interactive Dashboard**: Visualisasi data real-time dengan Plotly
- ✅ **Data Management**: Fitur untuk melihat, mengfilter, dan export data
- ✅ **System Configuration**: Interface admin untuk konfigurasi sensor dan sistem
- ✅ **User Authentication**: Login dan session management
- ✅ **Responsive Design**: Bootstrap UI untuk akses desktop/mobile
- ✅ **Virtual Keyboard**: Dukungan touchscreen untuk kenyamanan operator

### Sistem & Maintenance
- ✅ **Automated Backup**: Backup otomatis database MySQL
- ✅ **Logging System**: Pencatatan event koneksi, sensor, dan jaringan
- ✅ **External API Integration**: Pengiriman data ke sistem KLHK (Kementerian Lingkungan)
- ✅ **Retry Mechanism**: Sistem retry otomatis untuk pengiriman data gagal
- ✅ **USB Device Management**: Mounting USB otomatis untuk ekspor data

---

## 🖥️ Persyaratan Sistem

### Software Requirements
- **OS**: Linux (Debian/Ubuntu/Raspberry Pi OS)
- **Python**: 3.7+
- **Database**: MySQL 5.7+ atau MariaDB
- **Web Server**: Flask (built-in development server atau production server)
- **Docker**: Untuk containerization (opsional)

### Hardware Requirements
- **Minimum**: Raspberry Pi 4 (2GB RAM) atau SBC equivalent
- **Recommended**: 4GB+ RAM, USB ports untuk sensor

### Network Requirements
- Koneksi internet (untuk pengiriman data ke KLHK)
- Koneksi lokal untuk sensor (RS485, Modbus TCP)

### System Dependencies
```
python3, python3-pip
docker, docker-compose
mysql-client (untuk cli access)
git (untuk version control)
```

---

## 🚀 Instalasi

### Prerequisite Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip docker.io docker-compose mariadb-client git
```

### Quick Installation

```bash
# 1. Clone atau ekstrak project ke /home/pi/logix
cd /home/pi/logix

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run automated installer
chmod +x install.sh
./install.sh

# 4. Konfigurasi MySQL dan sensor (lihat bagian Konfigurasi)

# 5. Mulai services
sudo systemctl start logix-sensor
sudo systemctl start logix-web
```

### Manual Installation (Jika automated installer gagal)

```bash
# 1. Create config directory
mkdir -p config logs database/backup

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize SQLite config database
python3 backend/config.py

# 4. Setup MySQL database
mysql -u root -p < database/schema.sql  # (jika tersedia)

# 5. Update configuration di config/config.db (lihat bagian Konfigurasi)

# 6. Start services manually
cd backend
python3 main.py &  # Sensor reading service
python3 app.py &   # Web server
```

---

## ⚙️ Konfigurasi

### Database Configuration (MySQL)

Edit konfigurasi melalui web admin atau langsung di SQLite:

```bash
# Akses admin panel
# URL: http://localhost:5010/admin.html
```

**Parameter MySQL yang perlu dikonfigurasi:**
- `db_host`: Host MySQL (default: localhost)
- `db_port`: Port MySQL (default: 3306)
- `db_name`: Nama database (default: logix)
- `db_user`: Username MySQL
- `db_password`: Password MySQL

### Sensor Configuration

**Sensor Status (Active/Inactive)**
- `[sensor_name]_status`: Aktif/nonaktif sensor
- `[sensor_name]_port`: Port koneksi sensor (COM port atau IP:port untuk Modbus)

**Contoh:**
```
ph200_status = active
ph200_port = /dev/ttyUSB0

at500_status = active
at500_port = 192.168.1.100:502
```

### Web Server Configuration

- `port_number_app`: Port web server (default: 5010)
- `web_title`: Judul di browser
- `web_name`: Nama header aplikasi
- `device_id`: ID perangkat (untuk laporan KLHK)
- `location_name`: Nama lokasi pemantauan
- `geo_latitude`, `geo_longitude`: Koordinat lokasi
- `gap_web`: Interval refresh dashboard (detik)

### Data Collection Configuration

- `delay`: Interval pengumpulan sensor (menit, 1-60)
- `timezone`: Timezone sistem (default: Asia/Jakarta)
- `parameters`: List parameter yang dimonitor

### KLHK Integration (Opsional)

Untuk pengiriman otomatis data ke sistem KLHK:

```
has_status = active
has_api_url = https://api.klhk.gov.id/...
has_token_api = [your-token]
has_fields = datetime,pH,cod,tss,nh3n,flow

klhk_status = active
klhk_fields = datetime,pH,cod,tss,nh3n,flow
klhk_api_url = https://klhk.example.com/api
```

---

## 📖 Penggunaan

### Akses Aplikasi

**Dashboard (Monitoring)**
```
URL: http://<IP_SERVER>:5010/
Login dengan credential yang sudah dikonfigurasi
```

**Admin Panel (Konfigurasi)**
```
URL: http://<IP_SERVER>:5010/admin.html
Untuk mengatur sensor dan sistem
```

**Features Dashboard:**
- 📊 Real-time data visualization
- 📅 Historical data viewing dengan date range
- 📥 Data export (CSV)
- 🗺️ Geographic map display
- 📈 Graph dengan zoom & pan

### Monitoring Services

```bash
# Check service status
sudo systemctl status logix-sensor
sudo systemctl status logix-web
sudo systemctl status logix-backup
sudo systemctl status logix-klhk-send

# View logs
sudo journalctl -u logix-sensor -f
sudo journalctl -u logix-web -f

# Stop/Start services
sudo systemctl stop logix-sensor
sudo systemctl start logix-sensor
sudo systemctl restart logix-sensor
```

### Manual Testing

```bash
# Test sensor reading
cd backend
python3 ph200.py  # Test specific sensor
python3 main.py   # Test main collection loop

# Test Flask app
python3 app.py    # Start web server (port 5010)
```

---

## 📁 Struktur Folder

```
logix/
├── backend/                    # Backend Python services
│   ├── main.py                 # Main sensor data collection service
│   ├── app.py                  # Flask web server
│   ├── config.py               # Configuration management
│   ├── backup.py               # Database backup service
│   ├── logsSend.py             # Logging system
│   ├── clean_logs.py           # Log cleanup utility
│   │
│   ├── [sensor_modules]/       # Sensor-specific modules
│   ├── ph200.py                # pH & Temperature Sensor (Modbus)
│   ├── at500.py                # AT500 Weather Station
│   ├── rt200.py                # RT200 Radiation Sensor
│   ├── sem5096.py              # SEM5096 Water Level Sensor
│   ├── spectro.py              # Spectrophotometer (Modbus TCP)
│   ├── iscan.py                # IScan Turbidity Sensor
│   ├── ltnc.py                 # LTNC Sensor
│   ├── contlyte.py             # Contlyte Conductivity Sensor
│   ├── ds502.py                # DS502 Data Logger
│   ├── ammonia200.py           # Ammonia Analyzer
│   ├── cod200x.py              # COD Analyzer
│   ├── h1601.py                # H1601 Sensor
│   ├── tss200x.py              # TSS Analyzer
│   ├── xymd02.py               # Weather Sensor
│   ├── mace.py                 # MACE Sensor
│   │
│   ├── hasSend.py              # HAS API Integration (external service)
│   └── tes.py                  # Testing module
│
├── frontend/                   # Web UI (HTML/CSS/JS)
│   ├── index.html              # Main dashboard
│   ├── login.html              # Login page
│   ├── admin.html              # Admin panel
│   ├── logs.html               # System logs viewer
│   │
│   ├── components/             # Reusable HTML components
│   │   ├── header.html
│   │   └── sidebar.html
│   │
│   ├── sections/               # Page sections
│   │   ├── dashboard.html
│   │   ├── all-data.html
│   │   ├── config.html
│   │   ├── pending-data.html
│   │   ├── retry-data.html
│   │   └── klhk-success.html
│   │
│   ├── css/                    # Stylesheets
│   │   ├── style.css           # Main stylesheet
│   │   ├── dashboard.css
│   │   ├── config.css
│   │   ├── bootstrap.min.css
│   │   └── [other css files]
│   │
│   ├── js/                     # JavaScript
│   │   ├── main.js             # Main application logic
│   │   ├── dashboard.js
│   │   ├── config.js
│   │   ├── script.js
│   │   ├── keyboard.js         # Virtual keyboard
│   │   ├── plotly-latest.min.js
│   │   └── [library files]
│   │
│   └── images/                 # Static images & logos
│
├── config/                     # Configuration
│   └── config.db               # SQLite database (auto-created)
│
├── klhk/                       # KLHK Integration Services
│   ├── send.py                 # Send data to KLHK API
│   └── retry.py                # Retry failed sends
│
├── database/                   # Database files
│   ├── backup_state.json       # Backup state tracking
│   └── backup/                 # Database backups
│
├── logs/                       # Application logs
│   ├── [sensor_logs]/
│   ├── [connection_logs]/
│   └── [network_logs]/
│
├── requirements.txt            # Python dependencies
├── install.sh                  # Automated installer
├── uninstall.sh                # Uninstaller
└── README.md                   # This file
```

---

## 🏗️ Arsitektur Sistem

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    HARDWARE SENSORS                          │
│ (pH, Temperature, Flow, Weather, Turbidity, etc.)           │
└────────────────┬────────────────────────────────────────────┘
                 │ Serial RS485 / Modbus TCP
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (Python Services)                       │
│                                                              │
│  main.py: Scheduled Data Collection                         │
│  - Reads from 17+ sensor modules                           │
│  - Runs every N minutes (configurable)                      │
│  - Stores to MySQL database                                 │
│                                                              │
│  ├─ Sensor Modules (ph200.py, at500.py, etc.)             │
│  │  └─ Each module handles specific sensor protocol         │
│  │                                                          │
│  └─ Database Storage                                        │
│     └─ MySQL: Sensor data + timestamps                      │
│     └─ SQLite: Configuration                                │
│                                                              │
│  Additional Services:                                        │
│  - app.py: Flask web server                                 │
│  - backup.py: Automated database backup                     │
│  - hasSend.py: External API integration                     │
│  - logsSend.py: Centralized logging                         │
└────────┬──────────────────────────────────────────────┬─────┘
         │                                              │
         ▼                                              ▼
    ┌─────────┐                              ┌──────────────┐
    │ MySQL   │                              │ External API │
    │ Database│                              │ (KLHK, etc.) │
    └─────────┘                              └──────────────┘
         ▲                                              
         │ API Calls (SELECT, INSERT)                 
         │                                              
    ┌────────────────────────────────────────────────┐
    │         FRONTEND (Web UI)                       │
    │                                                 │
    │ app.py Routes:                                 │
    │ - GET /: Serve frontend                        │
    │ - POST /login: Authentication                  │
    │ - GET /api/data: Fetch sensor data             │
    │ - POST /api/config: Update configuration       │
    │                                                 │
    │ Web Pages:                                      │
    │ - Dashboard: Real-time data visualization      │
    │ - Admin: System configuration                  │
    │ - Logs: System logs viewer                      │
    │                                                 │
    │ Frontend Stack:                                 │
    │ - HTML5 UI                                      │
    │ - Bootstrap responsive layout                  │
    │ - Plotly for charting                          │
    │ - jQuery for AJAX calls                        │
    └────────────────────────────────────────────────┘
         ▲
         │ HTTP/WebSocket
         │
    ┌─────────────────┐
    │  Web Browser    │
    │  (Operator/IT)  │
    └─────────────────┘
```

### Service Architecture (Systemd Services)

```
Running Services:
├── logix-sensor.service
│   └─ Runs: backend/main.py
│   └─ Schedule: Every N minutes
│   └─ Purpose: Data collection from sensors
│
├── logix-web.service
│   └─ Runs: backend/app.py
│   └─ Port: 5010
│   └─ Purpose: Web server & API
│
├── logix-backup.service
│   └─ Runs: backend/backup.py
│   └─ Schedule: Every N hours/days
│   └─ Purpose: Database backup
│
├── logix-klhk-send.service
│   └─ Runs: klhk/send.py
│   └─ Purpose: Send data to KLHK API
│
├── logix-klhk-retry.service
│   └─ Runs: klhk/retry.py
│   └─ Purpose: Retry failed sends
│
└── logix-has-send.service
    └─ Runs: backend/hasSend.py
    └─ Purpose: Send data to external HAS API
```

---

## 🔌 Sensors Didukung

| Sensor | Model | Type | Protocol | Parameter |
|--------|-------|------|----------|-----------|
| pH Sensor | PH200 | Chemical | Modbus RS485 | pH, Temperature |
| Turbidity | ISCAN | Optical | Serial | Turbidity (NTU) |
| Conductivity | Contlyte | Electrochemistry | Serial | Conductivity |
| Temperature | RT200 | Thermal | Modbus TCP | Temperature, Radiation |
| Water Level | SEM5096 | Ultrasonic | Serial RS485 | Water Level, Distance |
| TSS Analyzer | TSS200X | Optical | Serial | TSS (mg/L) |
| COD Analyzer | COD200X | Chemical | Serial | COD (mg/L) |
| Weather Station | AT500 | Meteorological | Modbus TCP | Wind, Rainfall, Pressure |
| Spectrophotometer | Spectro | Optical | Modbus TCP | Various optical parameters |
| DS Logger | DS502 | Data Logger | Serial | Multiple |
| Ammonia Analyzer | Ammonia200 | Chemical | Serial | NH3-N |
| H1601 | H1601 | Sensor | Serial | Various |
| XYMD02 | XYMD02 | Meteorological | Serial | Weather data |
| MACE | MACE | Sensor | Modbus | Various |
| LTNC | LTNC | Sensor | Serial | Various |

**Catatan:** Beberapa sensor mungkin memerlukan konfigurasi khusus atau driver tambahan. Referensikan manual sensor untuk detail teknis.

---

## 🔧 Troubleshooting

### Sensor Not Reading

```bash
# 1. Check service status
sudo systemctl status logix-sensor

# 2. View error logs
sudo journalctl -u logix-sensor -n 100

# 3. Verify port configuration
cat config/config.db | grep "[sensor_name]_port"

# 4. Test port connectivity
ls -la /dev/ttyUSB*           # Check serial ports
nc -zv 192.168.1.100 502     # Test Modbus TCP

# 5. Restart service
sudo systemctl restart logix-sensor
```

### Web Dashboard Not Loading

```bash
# 1. Check Flask service
sudo systemctl status logix-web

# 2. Test port availability
curl -I http://localhost:5010

# 3. Check logs
sudo journalctl -u logix-web -n 50

# 4. Verify frontend files exist
ls -la frontend/

# 5. Restart Flask
sudo systemctl restart logix-web
```

### Database Connection Error

```bash
# 1. Test MySQL connection
mysql -h [host] -u [user] -p [database]

# 2. Verify credentials in config
grep -E 'db_host|db_user|db_name' config/config.db

# 3. Check MySQL service
sudo systemctl status mysql  # or mariadb

# 4. Create database if missing
mysql -u root -p < backend/schema.sql
```

### Login Issues

```bash
# Default credentials are stored in SQLite
# Reset via admin panel or update config table:
sqlite3 config/config.db
> SELECT * FROM config WHERE id=1;
> UPDATE config SET web_username='admin', web_password='[hashed]' WHERE id=1;
```

### USB Device Mounting Issues

```bash
# Check USB devices
lsblk
# or
sudo fdisk -l

# Manual mount
sudo mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb
```

---

## 📊 Data Export

### Via Web Interface
1. Login ke dashboard
2. Go to "All Data" section
3. Select date range
4. Click "Export as CSV"

### Via Command Line (MySQL)
```bash
# Export sensor data
mysql -h localhost -u logix -p logix -e \
  "SELECT * FROM sensor_data WHERE timestamp >= '2024-05-01';" > export.csv
```

### Via Backup Directory
```bash
# Automated backups stored at
ls -la database/backup/
```

---

## 🔒 Security Notes

⚠️ **Important Security Considerations:**

1. **Change Default Credentials**: Update admin username/password immediately
2. **API Tokens**: Store securely, rotate regularly
3. **Database**: Use strong MySQL passwords, restrict remote access
4. **Network**: Use VPN/firewall for remote access
5. **Logs**: Regularly review for unauthorized access attempts
6. **Updates**: Keep Python packages updated for security patches

---

## 📝 Catatan Teknis

### Uncertainties & Notes

- **Database Schema**: Tidak ada file schema.sql ditemukan. Struktur tabel disimpulkan dari kode app.py dan sensor modules
- **User Authentication**: Password hashing menggunakan SHA256, dapat diperkuat dengan bcrypt
- **API Documentation**: API endpoints bisa lebih terdokumentasi dengan Swagger/OpenAPI
- **Sensor Protocol Details**: Spesifikasi Modbus dan RS485 untuk masing-masing sensor bersifat proprietary

### Configuration Persistence

Konfigurasi disimpan di SQLite (`config/config.db`). Modifikasi langsung pada file ini akan dimuat ulang tanpa restart service (lihat `main.py` - reload config setiap kali sensor dibaca).

### Logging System

- Sensor logs → `logs/sensor_logs/`
- Connection logs → `logs/connection_logs/`
- Network logs → `logs/network_logs/`
- Flask app logs → systemd journal (akses via `journalctl`)

---

## 📞 Support & Contact

**Author**: Abu Bakar <abubakar.it.dev@gmail.com>  
**Version**: 1.0  
**License**: Private/Internal Project

---

## 📄 License

This project is private and for internal use only. Unauthorized distribution or commercial use is prohibited.

---

**Last Updated**: May 4, 2026
**Documentation Version**: 1.0
