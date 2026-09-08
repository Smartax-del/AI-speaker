import json
import os
import re

NOTES_FILE = "notes.json"
MAX_NOTES = 50


def extract_note_text(user_text):
    match = re.search(r"(?:запиши|добавь)\s*заметк[уи]?[,]?\s*(?:что\s+)?(.+)", user_text, re.IGNORECASE)
    return match.group(1).strip() if match else user_text

def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Ошибка загрузки заметок] {e}")
    return []


def save_notes(notes_list):
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения заметок] {e}")


notes = load_notes()


def add_note(text):
    global notes
    notes.append(text)
    if len(notes) > MAX_NOTES:
        notes = notes[-MAX_NOTES:]
    save_notes(notes)


def list_notes_text():
    if not notes:
        return "У тебя пока нет заметок."
    lines = [f"{i + 1}. {n}" for i, n in enumerate(notes)]
    return "Твои заметки: " + "; ".join(lines)


def remove_last_note():
    global notes
    if not notes:
        return None
    removed = notes.pop()
    save_notes(notes)
    return removed


def clear_notes():
    global notes
    notes = []
    save_notes(notes)


def remove_note_by_query(query, client, model="gpt-4o-mini"):
    global notes
    if not notes:
        return None

    numbered = "\n".join(f"{i}: {n}" for i, n in enumerate(notes))
    prompt = (
        f"Вот список заметок (с номерами):\n{numbered}\n\n"
        f"Пользователь попросил удалить: \"{query}\"\n"
        f"Укажи ТОЛЬКО номер заметки, которую нужно удалить, "
        f"или -1, если ни одна явно не подходит. Ответь одним числом, без пояснений."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        index = int(response.choices[0].message.content.strip())
        if 0 <= index < len(notes):
            removed = notes.pop(index)
            save_notes(notes)
            return removed
    except Exception as e:
        print(f"[Ошибка поиска заметки для удаления] {e}")

    return None