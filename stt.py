import io
import scipy.io.wavfile as wav
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("PROXYAPI_KEY"),
    base_url="https://api.proxyapi.ru/openai/v1",
)

def speech_to_text(audio_data, sample_rate):
    if audio_data is None:
        return ""

    buffer = io.BytesIO()
    wav.write(buffer, sample_rate, audio_data)
    buffer.seek(0)
    buffer.name = "speech.wav"

    print("[Распознавание речи...] Отправка в Whisper...")

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=buffer,
        language="ru",
    )

    print(f"[Распознано] {transcript.text}")
    return transcript.text