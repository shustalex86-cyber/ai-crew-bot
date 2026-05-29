from collections import deque
from typing import DefaultDict

MAX_EXCHANGES = 10

_store: DefaultDict[int, deque] = DefaultDict(lambda: deque(maxlen=MAX_EXCHANGES * 2))


def get_history(user_id: int) -> list[dict]:
    return list(_store[user_id])


def add_exchange(user_id: int, user_message: str, assistant_response: str) -> None:
    _store[user_id].append({"role": "user", "content": user_message})
    _store[user_id].append({"role": "assistant", "content": assistant_response})


def clear_history(user_id: int) -> None:
    _store[user_id].clear()


def history_size(user_id: int) -> int:
    return len(_store[user_id]) // 2


def get_last_response(user_id: int) -> str | None:
    messages = list(_store[user_id])
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            return msg["content"]
    return None
