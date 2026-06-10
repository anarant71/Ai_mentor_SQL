"""Mentor Chat API — AI-ментор через GigaChat."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware import require_active
from app.models.user import User
from app.services.gigachat import gigachat

router = APIRouter(prefix="/api/v1/mentor", tags=["mentor"])


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


MENTOR_SYSTEM_PROMPT = """Ты — AI-наставник по SQL на мебельной фабрике.
Ты помогаешь студенту разобраться с SQL-запросами.
Отвечай понятно, на русском языке, используй примеры SQL-кода.
Если студент ошибается — объясни причину и покажи как исправить.
Не давай готовых ответов на задания, но помогай разобраться.

Контекст: студент работает с базой данных мебельной фабрики.
Таблицы: materials (сырьё), products (готовая продукция),
sales (продажи), suppliers (поставщики), warehouse (склад).

Твоя задача — научить, а не решить за студента."""


@router.post("/chat", response_model=ChatResponse)
async def mentor_chat(
    body: ChatRequest,
    current_user: User = Depends(require_active),
):
    """Отправить сообщение AI-ментору и получить ответ.

    Передаётся вся история диалога (массив messages).
    Системный промпт добавляется автоматически.
    """
    messages = [{"role": "system", "content": MENTOR_SYSTEM_PROMPT}]
    for m in body.messages:
        messages.append({"role": m.role, "content": m.content})

    try:
        data = await gigachat.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        reply = data["choices"][0]["message"]["content"]
    except Exception as exc:
        reply = f"Извини, не могу ответить сейчас. Ошибка: {exc}"

    return ChatResponse(reply=reply)
