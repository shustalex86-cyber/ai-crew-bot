import logging
from agents import orchestrator, programmer, copywriter, designer, general_agent
from history import get_history, add_exchange

logger = logging.getLogger(__name__)

PROGRAMMING_KEYWORDS = [
    "код", "программ", "скрипт", "функци", "класс", "алгоритм",
    "python", "javascript", "typescript", "html", "css", "sql",
    "api", "баг", "ошибк", "debug", "разработ", "backend", "frontend",
    "база данных", "бд", "сервер", "deploy", "деплой", "git", "library",
    "библиотек", "модул", "import", "цикл", "массив", "список",
]

COPYWRITING_KEYWORDS = [
    "текст", "статья", "пост", "контент", "описани", "реклам",
    "слоган", "заголовок", "письмо", "email", "рассылк", "seo",
    "копирайт", "блог", "маркетинг", "продающ", "оффер", "напиши текст",
    "придумай текст", "напиши пост", "напиши статью",
]

DESIGN_KEYWORDS = [
    "дизайн", "ui", "ux", "интерфейс", "цвет", "шрифт", "лого",
    "иконк", "баннер", "макет", "верстк", "визуал", "стиль",
    "палитра", "типографик", "брендинг", "layout", "figma", "wireframe",
]


def detect_task_type(message: str) -> str:
    text = message.lower()
    scores = {"programming": 0, "copywriting": 0, "design": 0}

    for kw in PROGRAMMING_KEYWORDS:
        if kw in text:
            scores["programming"] += 1
    for kw in COPYWRITING_KEYWORDS:
        if kw in text:
            scores["copywriting"] += 1
    for kw in DESIGN_KEYWORDS:
        if kw in text:
            scores["design"] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "general"


def run_crew(user_message: str, user_id: int) -> str:
    task_type = detect_task_type(user_message)
    logger.info("Task type detected: %s for user %d", task_type, user_id)

    history = get_history(user_id)

    logger.info("Step 1: Orchestrator analyzing task...")
    orchestrator_brief = orchestrator(user_message)
    logger.info("Orchestrator done.")

    logger.info("Step 2: Specialist (%s) executing task...", task_type)
    if task_type == "programming":
        result = programmer(orchestrator_brief, user_message, history)
    elif task_type == "copywriting":
        result = copywriter(orchestrator_brief, user_message, history)
    elif task_type == "design":
        result = designer(orchestrator_brief, user_message, history)
    else:
        result = general_agent(orchestrator_brief, user_message, history)
    logger.info("Specialist done.")

    add_exchange(user_id, user_message, result)
    return result
