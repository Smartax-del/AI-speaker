import re
import threading
import queue

active_timer = None
timer_lock = threading.Lock()
timer_events = queue.Queue()

DURATION_PATTERN = re.compile(
    r"(\d+)\s*(секунд[уы]?|минут[уы]?|час[а]?ов?)",
    re.IGNORECASE
)

UNIT_SECONDS = {
    "секунд": 1, "секунды": 1, "секунду": 1,
    "минут": 60, "минуты": 60, "минуту": 60,
    "час": 3600, "часа": 3600, "часов": 3600,
}


def parse_duration(text):
    total_seconds = 0
    found = False
    for match in DURATION_PATTERN.finditer(text.lower()):
        number = int(match.group(1))
        unit = match.group(2)
        multiplier = UNIT_SECONDS.get(unit)
        if multiplier:
            total_seconds += number * multiplier
            found = True
    return total_seconds if found else None


def format_duration(seconds):
    minutes = seconds // 60
    secs = seconds % 60
    if minutes and secs:
        return f"{minutes} мин {secs} сек"
    elif minutes:
        return f"{minutes} мин"
    return f"{secs} сек"


def start_timer(seconds):
    global active_timer
    with timer_lock:
        if active_timer is not None:
            active_timer.cancel()
        t = threading.Timer(seconds, lambda: timer_events.put(seconds))
        t.daemon = True
        t.start()
        active_timer = t


def cancel_timer():
    global active_timer
    with timer_lock:
        if active_timer is not None:
            active_timer.cancel()
            active_timer = None
            return True
        return False