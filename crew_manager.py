import logging
from agents import (
    orchestrator, programmer, copywriter, designer, general_agent,
    generate_image, IMAGE_URL_PREFIX,
)
from history import get_history, add_exchange

logger = logging.getLogger(__name__)

IMAGE_GENERATION_KEYWORDS = [
    "нарисуй", "нарисуйте", "нарисовать",
    "сгенерируй", "сгенерируйте", "сгенерировать",
    "создай изображение", "создайте изображение", "создать изображение",
    "создай картинку", "создайте картинку",
    "сделай картинку", "сделай изображение",
    "генерируй", "генерация изображения",
    "нарисуй картинку", "нарисуй картинк",
    "изображение с", "картинку с", "картинку про",
    "dall-e", "dalle",
]

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


def is_image_generation_request(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in IMAGE_GENERATION_KEYWORDS)


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


def run_crew(
    user_message: str,
    user_id: int,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    if is_image_generation_request(user_message):
        logger.info("Image generation request from user %d", user_id)
        result = generate_image(user_message)
        add_exchange(user_id, user_message, "[изображение сгенерировано]")
        return result

    task_type = detect_task_type(user_message)
    logger.info("Task type detected: %s for user %d (image: %s)", task_type, user_id, bool(image_b64))

    history = get_history(user_id)

    logger.info("Step 1: Orchestrator analyzing task%s...", " + image" if image_b64 else "")
    orchestrator_brief = orchestrator(user_message, image_b64, media_type)
    logger.info("Orchestrator done.")

    if image_b64 and user_message in ("Проанализируй изображение", "Опиши изображение"):
        task_type = detect_task_type(orchestrator_brief)
        logger.info("Re-detected task type from orchestrator brief: %s", task_type)

    logger.info("Step 2: Specialist (%s) executing task...", task_type)
    if task_type == "programming":
        result = programmer(orchestrator_brief, user_message, history, image_b64, media_type)
    elif task_type == "copywriting":
        result = copywriter(orchestrator_brief, user_message, history, image_b64, media_type)
    elif task_type == "design":
        result = designer(orchestrator_brief, user_message, history, image_b64, media_type)
    else:
        result = general_agent(orchestrator_brief, user_message, history, image_b64, media_type)
    logger.info("Specialist done.")

    add_exchange(user_id, user_message, result)
    return result
