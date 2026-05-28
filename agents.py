import anthropic
from config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-4-5-20250929"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _build_user_content(
    user_message: str,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> list | str:
    if not image_b64:
        return user_message
    return [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_b64,
            },
        },
        {"type": "text", "text": user_message},
    ]


def _call(
    system_prompt: str,
    user_message: str,
    history: list[dict] | None = None,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    content = _build_user_content(user_message, image_b64, media_type)
    messages = list(history or []) + [{"role": "user", "content": content}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def orchestrator(
    user_message: str,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    system = (
        "Ты — Оркестратор, опытный менеджер проектов и стратег. "
        "Твоя задача: проанализировать запрос пользователя (и изображение, если есть), "
        "определить тип задачи (программирование, копирайтинг, дизайн или общий вопрос) "
        "и сформулировать чёткое, структурированное задание для профильного специалиста. "
        "Если передано изображение — опиши его содержимое в задании. "
        "Будь конкретным: укажи, что именно нужно сделать и какой результат ожидается. "
        "Отвечай строго на русском языке."
    )
    return _call(system, user_message, image_b64=image_b64, media_type=media_type)


def programmer(
    task: str,
    original_message: str,
    history: list[dict] | None = None,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    system = (
        "Ты — Senior-разработчик с обширным опытом в Python, JavaScript, TypeScript "
        "и других языках программирования. "
        "Ты пишешь чистый, эффективный и хорошо документированный код. "
        "Умеешь объяснять технические концепции простым языком. "
        "Если передано изображение (например, скриншот кода или ошибки) — проанализируй его. "
        "Всегда предоставляй рабочий код с примерами использования. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history, image_b64, media_type)


def copywriter(
    task: str,
    original_message: str,
    history: list[dict] | None = None,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    system = (
        "Ты — опытный копирайтер и контент-стратег с глубоким пониманием "
        "психологии читателя. "
        "Ты создаёшь убедительные, engaging и грамотные тексты для любых целей: "
        "маркетинг, SEO, социальные сети, статьи, письма. "
        "Если передано изображение — используй его как основу для текста или описания. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history, image_b64, media_type)


def designer(
    task: str,
    original_message: str,
    history: list[dict] | None = None,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    system = (
        "Ты — креативный дизайнер с опытом в UI/UX, графическом дизайне и брендинге. "
        "Ты понимаешь принципы визуальной иерархии, цветовой теории и пользовательского опыта. "
        "Если передано изображение — проанализируй его с точки зрения дизайна, "
        "дай конкретные рекомендации по улучшению. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history, image_b64, media_type)


def general_agent(
    task: str,
    original_message: str,
    history: list[dict] | None = None,
    image_b64: str | None = None,
    media_type: str = "image/jpeg",
) -> str:
    system = (
        "Ты — универсальный эксперт с широкими знаниями в разных областях. "
        "Ты даёшь развёрнутые, точные и полезные ответы на любые вопросы. "
        "Если передано изображение — опиши его подробно, извлеки текст (OCR) если есть, "
        "определи объекты, проанализируй содержимое. "
        "Если нужно — структурируй ответ по пунктам для удобства чтения. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history, image_b64, media_type)
