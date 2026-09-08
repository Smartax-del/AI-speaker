import subprocess
import webbrowser
import keyboard

APPS = {
    "блокнот": "notepad.exe",
    "калькулятор": "calc.exe",
    "проводник": "explorer.exe",
}


def open_app(name):
    name = name.lower().strip()
    if name == "браузер":
        webbrowser.open("https://google.com")
        return True
    exe = APPS.get(name)
    if exe:
        try:
            subprocess.Popen(exe)
            return True
        except Exception as e:
            print(f"[Ошибка открытия приложения] {e}")
            return False
    return False


def open_site(text):
    text = text.strip()
    if not text.startswith("http"):
        if " " not in text and "." in text:
            text = "https://" + text
        else:
            text = "https://www.google.com/search?q=" + text.replace(" ", "+")
    webbrowser.open(text)
    return True


def media_play_pause():
    keyboard.send("play/pause media")


def media_next():
    keyboard.send("next track media")


def media_prev():
    keyboard.send("previous track media")


def volume_up(steps=3):
    for _ in range(steps):
        keyboard.send("volume up")


def volume_down(steps=3):
    for _ in range(steps):
        keyboard.send("volume down")


def volume_mute():
    keyboard.send("volume mute")