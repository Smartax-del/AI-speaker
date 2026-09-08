import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from memory import get_facts_text

load_dotenv()

client = OpenAI(
    api_key=os.getenv("PROXYAPI_KEY"),
    base_url="https://api.proxyapi.ru/openai/v1",
)

BASE_SYSTEM_PROMPT = (
    "Ты — голосовой ассистент, встроенный в мини-колонку. "
    "Отвечай кратко и по делу, разговорным языком, "
    "как будто говоришь вслух, а не пишешь текст."
)

MAX_HISTORY_MESSAGES = 20
HISTORY_FILE = "history.json"


def build_system_message():
    content = BASE_SYSTEM_PROMPT
    facts_text = get_facts_text()
    if facts_text:
        content += "\n\n" + facts_text
    return {"role": "system", "content": content}


def load_history():
    system_message = build_system_message()
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                print(f"[История] Загружено {len(saved)} сообщений из прошлого сеанса.")
                return [system_message] + saved
        except Exception as e:
            print(f"[Ошибка загрузки истории] {e}")
    return [system_message]


def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[1:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения истории] {e}")


history = load_history()


def trim_history():
    global history
    if len(history) - 1 > MAX_HISTORY_MESSAGES:
        history = [history[0]] + history[-MAX_HISTORY_MESSAGES:]


def ask_ai(user_text):
    history[0] = build_system_message()  # обновляем факты перед каждым запросом
    history.append({"role": "user", "content": user_text})
    trim_history()

    print("[Запрос к ИИ...] Отправка...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history,
        )
    except Exception:
        history.pop()
        raise

    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    trim_history()
    save_history()

    print(f"[Ответ ИИ] {answer}")
    return answer


def clear_history():
    global history
    history = [build_system_message()]
    save_history()
    print("[История] Очищена.")