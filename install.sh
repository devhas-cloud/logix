#!/bin/bash
# ============================================
#  logix (Smart Portable Analyzer System) - Installer
# ============================================
# Nama Aplikasi : Smart Portable Analyzer System (logix)
# Deskripsi     : Sistem pemantauan cuaca dan kualitas udara otomatis.
# Fungsi        : Merekam data lingkungan seperti suhu, kelembaban, tekanan, dll.
# Dibuat oleh   : Abu Bakar <abubakar.it.dev@gmail.com>
# Versi         : 1.0
# Lisensi       : Private/Internal Project
# ============================================

# Strict mode
set -euo pipefail
trap 'echo "❌ Error pada baris $LINENO. Perintah gagal: $BASH_COMMAND"' ERR

# === Fungsi ===
check_port() {
    local port=$1
    if command -v ss >/dev/null 2>&1; then
        ss -tuln | grep -q ":$port " && return 0
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":$port " && return 0
    else
        echo "⚠️  Tidak dapat mengecek port: ss/netstat tidak ditemukan" >&2
        return 2
    fi
    return 1
}

error_exit() {
    echo "❌ $1" >&2
    exit 1
}

# === Konfigurasi ===
CONFIG_FILE="config/.env"
[[ -f "$CONFIG_FILE" ]] || error_exit "File konfigurasi '$CONFIG_FILE' tidak ditemukan!"
source "$CONFIG_FILE"
WEB_PORT="${PORT_NUMBER_APP}"
LOG_PORT="${PORT_NUMBER_LOG}"

# === Header ===
echo "============================================"
echo " Smart Portable Analyzer System (logix) - Installer"
echo "============================================"
echo "Dibuat oleh        : Abu Bakar <abubakar.it.dev@gmail.com>"
echo "Deskripsi          : Sistem pemantauan cuaca dan kualitas udara otomatis berbasis Python & API"
echo "Lokasi Instalasi   : /home/pi/logix"
echo "Service            : logix-sensor, logix-web, logix-backup, logix-gpio, logix-klhk-send, logix-klhk-retry, logix-has-send"
echo "Web Port           : 0.0.0.0:$WEB_PORT"
echo "Web Log Port       : 0.0.0.0:$LOG_PORT"
echo "PhpMyAdmin         : 0.0.0.0:8080"
echo "============================================"
echo ""

# === Cek port ===
echo "Mengecek ketersediaan port..."
check_port "$WEB_PORT" && error_exit "Port $WEB_PORT sudah digunakan. Ubah konfigurasi port di $CONFIG_FILE"
check_port "$LOG_PORT" && error_exit "Port $LOG_PORT sudah digunakan. Ubah konfigurasi port di $CONFIG_FILE"
echo "Semua port tersedia. Melanjutkan instalasi..."
echo ""

# === Validasi lingkungan ===
echo "Memvalidasi dependensi sistem..."
missing_deps=()
command -v python3 >/dev/null 2>&1 || missing_deps+=("python3")
command -v pip >/dev/null 2>&1 || missing_deps+=("python3-pip")
command -v docker >/dev/null 2>&1 || missing_deps+=("docker.io")
command -v docker-compose >/dev/null 2>&1 || missing_deps+=("docker-compose")
command -v mysql >/dev/null 2>&1 || missing_deps+=("mariadb-client")

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo "Dependensi berikut belum terpasang:"
    for dep in "${missing_deps[@]}"; do
        echo " - $dep"
    done
    echo "Menginstall dependensi..."
    sudo apt update
    sudo apt install -y "${missing_deps[@]}"
    echo "✅ Instalasi selesai."
else
    echo "✅ Semua dependensi sudah terpenuhi."
fi
echo ""

# === Cek service existing ===
CHECK_SERVICES=("logix-sensor.service" "logix-web.service" "logix-web-log.service" "logix-backup.service" "logix-klhk-send.service" "logix-klhk-retry.service")
echo "Mengecek apakah service sudah ada..."
found_existing=false
for service in "${CHECK_SERVICES[@]}"; do
    [[ -f "/etc/systemd/system/$service" ]] && { echo "Ditemukan service: $service"; found_existing=true; }
done

if [ "$found_existing" = true ]; then
    echo "🚫 Instalasi dibatalkan. Service sudah ada."
    exit 1
fi
echo "Tidak ada konflik service. Lanjut instalasi..."
echo ""

# === Setup Directories ===
APP_BASE="/home/pi/logix"
LOG_DIR="$APP_BASE/logs"
mkdir -p "$APP_BASE" "$LOG_DIR"
echo "Direktori instalasi siap."
echo ""

# === Python Virtual Environment ===
echo "Membuat virtual environment..."
python3 -m venv "$APP_BASE/venv"
source "$APP_BASE/venv/bin/activate"
pip install --upgrade pip setuptools wheel
echo "Virtual environment berhasil dibuat."
echo ""

# === Install Python Dependencies ===
REQ_FILE="$APP_BASE/requirements.txt"
if [[ -f "$REQ_FILE" ]]; then
    echo "Menginstal dependensi Python..."
    pip install -r "$REQ_FILE"
    echo "Semua dependensi Python terinstal."
else
    echo "requirements.txt tidak ditemukan. Melewati instalasi dependensi."
fi
echo ""

# === CLI Link ===
echo "Menautkan CLI 'logix' ke /usr/bin/logix..."
[[ -f "$APP_BASE/logix" ]] && install -m 755 "$APP_BASE/logix" /usr/bin/logix
echo ""

# === Docker Database ===
echo "Memeriksa container database..."
if ! docker ps -a --format '{{.Names}}' | grep -q "^db_logix$"; then
    docker run -d --restart=always --name db_logix --network host -it devhas01/db-logix:1.0
    sleep 5
    docker exec -it db_logix service mysql start
    echo "Container database berhasil dijalankan."
else
    echo "Container db_logix sudah ada. Melewati pembuatan."
fi
echo ""

# === Systemd Services (compatible Pi) ===
echo "Membuat service systemd..."
SERVICES=(
    "logix-sensor|backend/main.py|sensor.log"
    "logix-web|backend/app.py|web.log"
    "logix-web-log|backend/log.py|log.log"
    "logix-backup|backend/backup.py|backup.log"
    "logix-klhk-send|klhk/send.py|send.log"
    "logix-klhk-retry|klhk/retry.py|retry.log"
    "logix-has-send|backend/hasSend.py|has-send.log"
)
for item in "${SERVICES[@]}"; do
    IFS="|" read -r service script log <<< "$item"
    cat <<EOF > "/etc/systemd/system/$service.service"
[Unit]
Description=logix $service Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_BASE/$(dirname "$script")
ExecStart=$APP_BASE/venv/bin/python -u $(basename "$script")
StandardOutput=append:$LOG_DIR/$log
StandardError=append:$LOG_DIR/$log
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$service"
    systemctl restart "$service"
done
echo "✅ Semua service systemd aktif."
echo ""

# === Log Cleanup Timer ===
chmod +x "$APP_BASE/backend/log_cleanup.py"
cp "$APP_BASE/logix-log-cleanup.service" /etc/systemd/system/
cp "$APP_BASE/logix-log-cleanup.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable logix-log-cleanup.timer
systemctl start logix-log-cleanup.timer
echo "Log cleanup timer aktif."
echo ""

# === Selesai ===
echo "🎉 Instalasi logix selesai!"
echo "Gunakan perintah 'logix' di terminal."
echo "============================================"
echo "Aplikasi dapat diakses di:"
echo "   - Web Interface: http://localhost:$WEB_PORT"
echo "   - Log Viewer: http://localhost:$LOG_PORT"
echo "   - PhpMyAdmin: http://localhost:8080"
echo "============================================"