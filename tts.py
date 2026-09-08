from openai import OpenAI
import os
from dotenv import load_dotenv
import pygame
import threading

load_dotenv()

audio_lock = threading.Lock()

client = OpenAI(
    api_key=os.getenv("PROXYAPI_KEY"),
    base_url="https://api.proxyapi.ru/openai/v1",
)

try:
    pygame.mixer.init()
except Exception as e:
    print(f"[Предупреждение] Не удалось инициализировать аудио: {e}")


def speak(text, filename="speech.mp3", poll_events=None, get_volume=None):
    if not text.strip():
        return False

    with audio_lock:
        print("[Генерация речи...] Отправка в TTS...")
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="shimmer",
            input=text,
            instructions="Voice: говори как радостный человек, который рад тебя слышать — "
                "с живыми, естественными перепадами интонации, а не ровным голосом. "
                "Emotion: искренний энтузиазм и лёгкая улыбка слышны в каждой фразе, "
                "как будто только что услышал хорошую новость. "
                "Pacing: не читай текст ровно — делай акценты на ключевых словах, "
                "чуть ускоряйся на интересных моментах, чуть замедляйся для выделения важного. "
                "Avoid: монотонность, ровный дикторский тон, безэмоциональное чтение."
        ) as response:
            response.stream_to_file(filename)

        cancelled = False
        try:
            print("[Проигрывание...]")
            pygame.mixer.music.load(filename)

            if poll_events:
                poll_events()
            if get_volume:
                pygame.mixer.music.set_volume(get_volume())

            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if poll_events and poll_events():
                    pygame.mixer.music.stop()
                    cancelled = True
                    print("[Отменено] Воспроизведение остановлено пользователем.")
                    break
                if get_volume:
                    pygame.mixer.music.set_volume(get_volume())
                pygame.time.wait(50)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[Ошибка воспроизведения] {e}")

        return cancelled