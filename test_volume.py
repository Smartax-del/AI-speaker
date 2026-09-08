import time
from record import poll_volume

print("Крути ручку потенциометра, буду печатать громкость. Ctrl+C для выхода.")

try:
    while True:
        vol = poll_volume()
        print(f"Текущая громкость: {vol:.2f}")
        time.sleep(0.3)
except KeyboardInterrupt:
    print("\nВыход")