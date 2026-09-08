import sounddevice as sd
import numpy as np
import serial.tools.list_ports
import time
import threading

SAMPLE_RATE = 16000
SERIAL_PORT = None  # Автоматическое определение порта
BAUD_RATE = 9600
MAX_RECORD_SECONDS = 60

ser = None
serial_lock = threading.Lock()
current_volume = 1.0


def find_arduino_port():
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()
        if "arduino" in desc or "ch340" in desc or "usb-serial" in desc or "arduino" in manufacturer:
            return port.device
    return None

def get_serial():
    global ser
    if ser is None:
        port = SERIAL_PORT or find_arduino_port()
        if port is None:
            raise serial.SerialException("Arduino не найдена ни на одном COM-порту")
        ser = serial.Serial(port, BAUD_RATE, timeout=0)
        time.sleep(2)
        print(f"[Arduino] Подключено через {port}")
    return ser


def send_command(command):
    try:
        s = get_serial()
        with serial_lock:
            s.write((command + "\n").encode("utf-8"))
    except Exception as e:
        print(f"[Ошибка отправки команды на Arduino] {e}")


def read_serial_line(s):
    with serial_lock:
        if s.in_waiting > 0:
            try:
                return s.readline().decode("utf-8", errors="ignore").strip()
            except Exception:
                return None
    return None


def flush_serial():
    try:
        s = get_serial()
        with serial_lock:
            while s.in_waiting > 0:
                s.readline()
    except Exception:
        pass


def poll_serial_events():
    """Считывает ВСЕ ожидающие строки за один проход. Возвращает True, если было PRESS."""
    global current_volume
    press_detected = False
    try:
        s = get_serial()
        while True:
            line = read_serial_line(s)
            if line is None:
                break
            if line == "PRESS":
                press_detected = True
            elif line.startswith("VOL:"):
                try:
                    raw_value = int(line.split(":")[1])
                    current_volume = raw_value / 1023.0
                except ValueError:
                    pass
    except Exception:
        pass
    return press_detected


def get_current_volume():
    return current_volume


def record_audio(idle_callback=None):
    try:
        s = get_serial()
        print("[Ожидание] Нажми и держи кнопку на колонке, чтобы говорить...")

        while True:
            line = read_serial_line(s)
            if line == "PRESS":
                break
            if idle_callback:
                idle_callback()
            time.sleep(0.01)

        send_command("LISTEN")
        print("[Запись...] Говори!")
        frames = []
        start_time = time.time()

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while True:
                block, _ = stream.read(1024)
                frames.append(block)

                if time.time() - start_time > MAX_RECORD_SECONDS:
                    print(f"[Таймаут] Запись превысила {MAX_RECORD_SECONDS} секунд, останавливаю.")
                    break

                line = read_serial_line(s)
                if line == "RELEASE":
                    break

        print("[Запись остановлена]")

        if not frames:
            print("[Ошибка записи] Аудио не захвачено.")
            return None, SAMPLE_RATE

        audio_data = np.concatenate(frames, axis=0)
        return audio_data, SAMPLE_RATE

    except serial.SerialException as e:
        print(f"[Ошибка Serial] Не удалось подключиться к Arduino: {e}")
        return None, SAMPLE_RATE
    except Exception as e:
        print(f"[Неожиданная ошибка записи] {e}")
        return None, SAMPLE_RATE