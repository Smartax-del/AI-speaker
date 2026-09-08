import time
import sys
import re
from record import record_audio, send_command, flush_serial, get_serial, poll_serial_events, get_current_volume
from stt import speech_to_text
from chat import ask_ai, client as chat_client
from tts import speak
from logger import check_internet, setup_logger
from memory import add_fact, clear_facts, remove_fact_by_query, extract_fact_text, extract_forget_query
import timer
import notes
import os
import os_control

logger = setup_logger()


def set_state(state, command=None):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{state}]")
    logger.info(state)
    if command:
        send_command(command)

def go_ready():
    set_state("READY", "READY")

def go_error(message):
    set_state(f"ERROR: {message}", "ERROR")
    logger.error(message)
    time.sleep(2)
    go_ready()

def say(text):
    set_state("SPEAKING", "SPEAK")
    speak(text, poll_events=poll_serial_events, get_volume=get_current_volume)

def handle_timer_expired(duration_seconds):
    set_state("SPEAKING", "SPEAK")
    send_command("ALARM")
    time.sleep(0.3)
    try:
        speak(f"Таймер на {timer.format_duration(duration_seconds)} истёк!",
            poll_events=poll_serial_events, get_volume=get_current_volume)
    except Exception as e:
        print(f"[Ошибка объявления таймера] {e}")

def check_timer_queue():
    if not timer.timer_events.empty():
        duration = timer.timer_events.get()
        handle_timer_expired(duration)
        set_state("LISTENING", "LISTEN")


print("=== Голосовой ассистент запущен ===")

if not os.getenv("PROXYAPI_KEY"):
    print("[Нет API-ключа] Проверь файл .env — отсутствует PROXYAPI_KEY.")
    logger.error("Отсутствует PROXYAPI_KEY")
    sys.exit(1)

if not check_internet():
    print("[Нет интернета] Проверь подключение к сети и запусти заново.")
    logger.error("Нет интернета при старте")
    sys.exit(1)

try:
    get_serial()
except Exception as e:
    print(f"[Arduino не найдена] Проверь подключение по USB и COM-порт. {e}")
    logger.error(f"Arduino не найдена: {e}")
    sys.exit(1)

print("Зажми и держи кнопку, чтобы говорить. Ctrl+C — выход.\n")

go_ready()

try:
    while True:
        flush_serial()
        set_state("LISTENING")
        audio_data, sr = record_audio(idle_callback=check_timer_queue)

        if audio_data is None:
            go_error("Запись не удалась")
            continue

        set_state("TRANSCRIBING")
        try:
            user_text = speech_to_text(audio_data, sr)
        except Exception as e:
            go_error(f"Ошибка распознавания: {e}")
            continue

        if not user_text.strip():
            go_error("Речь не распознана")
            continue

        text_lower = user_text.lower()

        if "таймер" in text_lower:
            if "останови" in text_lower or "отмени" in text_lower:
                cancelled_timer = timer.cancel_timer()
                reply = "Таймер остановлен." if cancelled_timer else "Активных таймеров нет."
                say(reply)
                go_ready()
                print()
                continue

            seconds = timer.parse_duration(user_text)
            if seconds:
                timer.start_timer(seconds)
                say(f"Ставлю таймер на {timer.format_duration(seconds)}.")
            else:
                say("Не понял, на сколько ставить таймер.")
            go_ready()
            print()
            continue

        if text_lower.startswith("запомни"):
            fact_text = extract_fact_text(user_text)
            add_fact(fact_text)
            say("Запомнил.")
            go_ready()
            print()
            continue

        if "забудь" in text_lower or "очисти память" in text_lower:
            if any(w in text_lower for w in ["всё", "все", "полностью"]):
                clear_facts()
                reply = "Хорошо, я всё забыл."
            else:
                query = extract_forget_query(user_text)
                removed = remove_fact_by_query(query, chat_client)
                reply = "Забыл." if removed else "Не нашёл, что именно забыть."
            say(reply)
            go_ready()
            print()
            continue

        if "заметк" in text_lower:
            if "прочитай" in text_lower or "какие" in text_lower or "список" in text_lower:
                say(notes.list_notes_text())
                go_ready()
                print()
                continue

            if "очисти" in text_lower or ("удали" in text_lower and "все" in text_lower):
                notes.clear_notes()
                say("Все заметки удалены.")
                go_ready()
                print()
                continue

            if "удали последн" in text_lower:
                removed = notes.remove_last_note()
                reply = f"Удалил заметку: {removed}." if removed else "Заметок нет."
                say(reply)
                go_ready()
                print()
                continue

            if "удали" in text_lower:
                removed = notes.remove_note_by_query(user_text, chat_client)
                reply = f"Удалил заметку: {removed}." if removed else "Не нашёл такую заметку."
                say(reply)
                go_ready()
                print()
                continue

            if "запиши" in text_lower or "добавь" in text_lower:
                note_text = notes.extract_note_text(user_text)
                notes.add_note(note_text)
                say(f"Записал: {note_text}")
                go_ready()
                print()
                continue

        if "открой" in text_lower:
            if "браузер" in text_lower:
                os_control.open_app("браузер")
                say("Открываю браузер.")
            elif "блокнот" in text_lower:
                os_control.open_app("блокнот")
                say("Открываю блокнот.")
            elif "калькулятор" in text_lower:
                os_control.open_app("калькулятор")
                say("Открываю калькулятор.")
            elif "проводник" in text_lower:
                os_control.open_app("проводник")
                say("Открываю проводник.")
            elif "сайт" in text_lower:
                site_query = re.sub(r".*сайт\s*", "", user_text, flags=re.IGNORECASE).strip()
                os_control.open_site(site_query)
                say(f"Открываю {site_query}.")
            else:
                say("Не понял, что открыть.")
            go_ready()
            print()
            continue

        if "найди в интернете" in text_lower or "поищи в интернете" in text_lower:
            query = re.sub(r".*(найди|поищи) в интернете\s*", "", user_text, flags=re.IGNORECASE).strip()
            os_control.open_site(query)
            say(f"Ищу: {query}")
            go_ready()
            print()
            continue

        if "музык" in text_lower or "трек" in text_lower or "пауза" in text_lower:
            if "следующ" in text_lower:
                os_control.media_next()
                say("Следующий трек.")
            elif "предыдущ" in text_lower or "прошлый" in text_lower:
                os_control.media_prev()
                say("Предыдущий трек.")
            else:
                os_control.media_play_pause()
                say("Готово.")
            go_ready()
            print()
            continue

        if "громче" in text_lower or "тише" in text_lower or "без звука" in text_lower or "выключи звук" in text_lower:
            if "без звука" in text_lower or "выключи звук" in text_lower:
                os_control.volume_mute()
                say("Звук выключен.")
            elif "громче" in text_lower:
                os_control.volume_up()
                say("Прибавил громкость.")
            elif "тише" in text_lower:
                os_control.volume_down()
                say("Убавил громкость.")
            go_ready()
            print()
            continue

        set_state("THINKING", "THINK")
        try:
            answer = ask_ai(user_text)
        except Exception as e:
            go_error(f"Ошибка ИИ: {e}")
            continue

        set_state("SPEAKING", "SPEAK")
        try:
            cancelled = speak(answer, poll_events=poll_serial_events, get_volume=get_current_volume)
        except Exception as e:
            go_error(f"Ошибка озвучки: {e}")
            continue

        if cancelled:
            print("[Отменено пользователем]\n")

        go_ready()
        print()

except KeyboardInterrupt:
    send_command("READY")
    print("\n[Выход] Ассистент остановлен пользователем. До встречи!")