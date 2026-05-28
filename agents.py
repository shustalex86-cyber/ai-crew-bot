import anthropic
from config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-4-5-20250929"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _call(system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
    messages = list(history or []) + [{"role": "user", "content": user_message}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def orchestrator(user_message: str) -> str:
    system = (
        "Ты — Оркестратор, опытный менеджер проектов и стратег. "
        "Твоя задача: проанализировать запрос пользователя, определить его тип "
        "(программирование, копирайтинг, дизайн или общий вопрос) и сформулировать "
        "чёткое, структурированное задание для профильного специалиста. "
        "Будь конкретным: укажи, что именно нужно сделать и какой результат ожидается. "
        "Отвечай строго на русском языке."
    )
    return _call(system, user_message)


def programmer(task: str, original_message: str, history: list[dict] | None = None) -> str:
    system = (
        "Ты — Senior-разработчик с обширным опытом в Python, JavaScript, TypeScript "
        "и других языках программирования. "
        "Ты пишешь чистый, эффективный и хорошо документированный код. "
        "Умеешь объяснять технические концепции простым языком. "
        "Всегда предоставляй рабочий код с примерами использования. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history)


def copywriter(task: str, original_message: str, history: list[dict] | None = None) -> str:
    system = (
        "Ты — опытный копирайтер и контент-стратег с глубоким пониманием "
        "психологии читателя. "
        "Ты создаёшь убедительные, engaging и грамотные тексты для любых целей: "
        "маркетинг, SEO, социальные сети, статьи, письма. "
        "Твои тексты цепляют внимание, убеждают и вдохновляют. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history)


def designer(task: str, original_message: str, history: list[dict] | None = None) -> str:
    system = (
        "Ты — креативный дизайнер с опытом в UI/UX, графическом дизайне и брендинге. "
        "Ты понимаешь принципы визуальной иерархии, цветовой теории и пользовательского опыта. "
        "Даёшь конкретные, применимые советы по дизайну, UI/UX, визуальной коммуникации. "
        "Описываешь концепции детально, чтобы их можно было реализовать. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history)


def general_agent(task: str, original_message: str, history: list[dict] | None = None) -> str:
    system = (
        "Ты — универсальный эксперт с широкими знаниями в разных областях. "
        "Ты даёшь развёрнутые, точные и полезные ответы на любые вопросы. "
        "Если нужно — структурируй ответ по пунктам для удобства чтения. "
        "Если в истории диалога есть предыдущие сообщения — учитывай контекст. "
        "Отвечай строго на русском языке."
    )
    prompt = (
        f"Исходный запрос пользователя: {original_message}\n\n"
        f"Задание от оркестратора: {task}"
    )
    return _call(system, prompt, history)
