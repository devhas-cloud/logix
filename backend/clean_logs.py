import os

LOG_DIR = "/home/pi/logix/logs"
MAX_LINES = 10000

LOG_FILES = [
    "web.log",
    "sensor.log",
    "send.log",
    "retry.log",
    "has-send.log",
    "backup.log"
]

def clean_all_logs():
    if not os.path.exists(LOG_DIR):
        print(f"❌ Direktori log tidak ditemukan: {LOG_DIR}")
        return

    for filename in LOG_FILES:
        filepath = os.path.join(LOG_DIR, filename)
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            total_lines = len(lines)
            if total_lines > MAX_LINES:
                lines_to_remove = total_lines - MAX_LINES
                # Keep the last MAX_LINES
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-MAX_LINES:])
                print(f"✓ ../logs/{filename}: {total_lines} → {MAX_LINES} baris ({lines_to_remove} baris dihapus)")
            else:
                print(f"✓ ../logs/{filename}: {total_lines} baris (tidak perlu dibersihkan)")
        except Exception as e:
            print(f"❌ Gagal membersihkan ../logs/{filename}: {e}")

if __name__ == "__main__":
    clean_all_logs()
