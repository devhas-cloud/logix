#!/bin/bash

# ============================================
#  logix (Smart Portable Analyzer System) - Uninstaller
# ============================================
# Nama Aplikasi : Smart Portable Analyzer System (logix)
# Fungsi        : Menghapus semua komponen logix dari sistem
# Dibuat oleh   : Abu Bakar <abubakar.it.dev@gmail.com>
# Versi         : 1.1
# ============================================

echo "============================================"
echo " Smart Portable Analyzer System (logix) - Uninstaller"
echo "============================================"
echo "📌 Dibuat oleh : Abu Bakar <abubakar.it.dev@gmail.com>"
echo ""

set -e  # Hentikan jika terjadi error

APP_BASE="/home/pi/logix"
SERVICES=("logix-sensor.service" "logix-web.service" "logix-backup.service" "logix-klhk-send.service" "logix-klhk-retry.service" "logix-has-send.service")
TIMERS=("logix-log-cleanup.timer")

# === Hentikan dan nonaktifkan semua timer ===
echo "🛑 Menghentikan dan menonaktifkan systemd timers..."
for timer in "${TIMERS[@]}"; do
    if systemctl is-enabled --quiet "$timer" 2>/dev/null; then
        echo "🔻 Menonaktifkan & menghentikan $timer..."
        systemctl stop "$timer"
        systemctl disable "$timer"
        rm -f "/etc/systemd/system/$timer"
        # Hapus juga service yang terkait
        service_file="${timer%.timer}.service"
        rm -f "/etc/systemd/system/$service_file"
        echo "✅ $timer dihapus."
    else
        echo "ℹ️  $timer tidak ditemukan atau sudah nonaktif."
    fi
done

# === Hentikan dan nonaktifkan semua service ===
echo "🛑 Menghentikan dan menonaktifkan systemd services..."
for service in "${SERVICES[@]}"; do
    if systemctl is-enabled --quiet "$service"; then
        echo "🔻 Menonaktifkan & menghentikan $service..."
        systemctl stop "$service"
        systemctl disable "$service"
        rm -f "/etc/systemd/system/$service"
        echo "✅ $service dihapus."
    else
        echo "ℹ️  $service tidak ditemukan atau sudah nonaktif."
    fi
done

# Reload systemd
echo "🔄 Reload systemd daemon..."
systemctl daemon-reload
systemctl reset-failed



# === Hapus symlink CLI ===
if [[ -f "/usr/bin/logix" ]]; then
    echo "🗑️  Menghapus CLI /usr/bin/logix..."
    rm -f /usr/bin/logix
else
    echo "ℹ️  CLI /usr/bin/logix tidak ditemukan."
fi

# === Konfirmasi penghapusan database Docker ===
if docker ps -a --format '{{.Names}}' | grep -q "^db_logix$"; then
    echo ""
    echo "⚠️  Container Docker 'db_logix' ditemukan."
    read -p "❓ Apakah Anda ingin menghapus database ini? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo "🐳 Menghentikan dan menghapus container 'db_logix'..."
        docker stop db_logix
        docker rm db_logix
        echo "✅ Container 'db_logix' telah dihapus."
    else
        echo "ℹ️  Container 'db_logix' dibiarkan tetap ada."
    fi
else
    echo "ℹ️  Container 'db_logix' tidak ditemukan."
fi

echo ""
echo "✅ Uninstall selesai! Semua komponen utama logix telah dihapus dari sistem."
echo "Terima kasih telah menggunakan logix Project!"