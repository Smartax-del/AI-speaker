import json
import os
import re

MEMORY_FILE = "memory.json"
MAX_FACTS = 30


def load_facts():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Ошибка загрузки памяти] {e}")
    return []


def save_facts(facts_list):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(facts_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения памяти] {e}")


facts = load_facts()


def add_fact(text):
    global facts
    facts.append(text)
    if len(facts) > MAX_FACTS:
        facts = facts[-MAX_FACTS:]
    save_facts(facts)


def clear_facts():
    global facts
    facts = []
    save_facts(facts)


def get_facts_text():
    if not facts:
        return ""
    return "Известные факты:\n" + "\n".join(f"- {f}" for f in facts)


def remove_fact_by_query(query, client, model="gpt-4o-mini"):
    """Просит ИИ найти, какой из сохранённых фактов соответствует запросу на удаление."""
    global facts
    if not facts:
        return None

    numbered = "\n".join(f"{i}: {f}" for i, f in enumerate(facts))
    prompt = (
        f"Вот список фактов (с номерами):\n{numbered}\n\n"
        f"Пользователь попросил забыть: \"{query}\"\n"
        f"Укажи ТОЛЬКО номер факта, который нужно удалить, "
        f"или -1, если ни один факт явно не подходит. Ответь одним числом, без пояснений."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        index = int(response.choices[0].message.content.strip())
        if 0 <= index < len(facts):
            removed = facts.pop(index)
            save_facts(facts)
            return removed
    except Exception as e:
        print(f"[Ошибка поиска факта для удаления] {e}")

    return None


def extract_fact_text(user_text):
    match = re.search(r"запомни[,]?\s*(?:что\s+)?(.+)", user_text, re.IGNORECASE)
    fact = match.group(1).strip() if match else user_text
    fact = re.sub(r"^я\s+", "", fact, flags=re.IGNORECASE)
    return fact


def extract_forget_query(user_text):
    match = re.search(r"забудь[,]?\s*(?:что\s+)?(.+)", user_text, re.IGNORECASE)
    return match.group(1).strip() if match else user_text