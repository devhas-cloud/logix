#!/usr/bin/env python3
"""
Script untuk membersihkan log files secara otomatis
Menyisakan hanya 1000 baris terakhir dari setiap file log
"""
import os
from datetime import datetime

LOG_FILES = {
    'web': '/opt/logix/logs/web.log',
    'sensor': '/opt/logix/logs/sensor.log',
    'send': '/opt/logix/logs/send.log',
    'retry': '/opt/logix/logs/retry.log',
    'backup': '/opt/logix/logs/backup.log',
    'gpio': '/opt/logix/logs/gpio.log',
    'has': '/opt/logix/logs/has-send.log'
}

def cleanup_log_file(filepath, max_lines=1000):
    """Membersihkan file log dan menyisakan max_lines baris terakhir"""
    if not os.path.exists(filepath):
        print(f"⚠️  File tidak ditemukan: {filepath}")
        return False
    
    try:
        # Baca semua baris
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        original_lines = len(lines)
        
        # Jika file sudah kecil, skip
        if original_lines <= max_lines:
            print(f"✓ {filepath}: {original_lines} baris (tidak perlu dibersihkan)")
            return True
        
        # Ambil hanya max_lines baris terakhir
        last_lines = lines[-max_lines:]
        
        # Tulis ulang file dengan baris yang tersisa
        with open(filepath, 'w') as f:
            f.writelines(last_lines)
        
        deleted_lines = original_lines - max_lines
        print(f"✓ {filepath}: {original_lines} → {max_lines} baris ({deleted_lines} baris dihapus)")
        return True
        
    except Exception as e:
        print(f"❌ Error membersihkan {filepath}: {e}")
        return False

def main():
    print(f"\n{'='*60}")
    print(f"Log Cleanup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    success_count = 0
    total_count = len(LOG_FILES)
    
    for log_name, filepath in LOG_FILES.items():
        if cleanup_log_file(filepath):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Selesai: {success_count}/{total_count} file berhasil diproses")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
