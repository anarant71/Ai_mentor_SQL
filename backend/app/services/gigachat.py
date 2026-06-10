"""GigaChat client — OAuth token management + chat completion."""

import asyncio
import logging
import time
import uuid
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class GigaChatClient:
    """Async client for GigaChat API (Sberbank LLM).

    Handles OAuth token acquisition and refresh (tokens expire in 30 min).
    Uses httpx with configurable SSL verification.
    """

    def __init__(self) -> None:
        self._auth_key: str = settings.GIGACHAT_AUTH_KEY
        self._scope: str = settings.GIGACHAT_SCOPE
        self._api_base: str = settings.GIGACHAT_API_BASE.rstrip("/")
        self._auth_url: str = settings.GIGACHAT_AUTH_URL
        self._model: str = settings.GIGACHAT_MODEL
        self._verify: bool = settings.GIGACHAT_SSL_VERIFY

        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def _token_valid(self) -> bool:
        return bool(self._access_token) and (time.time() + 60 < self._expires_at)

    async def _fetch_token(self) -> None:
        """Fetch a new access token from the OAuth endpoint."""
        rq_uid = str(uuid.uuid4())

        async with httpx.AsyncClient(verify=self._verify) as client:
            resp = await client.post(
                self._auth_url,
                headers={
                    "Authorization": f"Basic {self._auth_key}",
                    "RqUID": rq_uid,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                data={"scope": self._scope},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._expires_at = float(data["expires_at"])

        logger.info("GigaChat token acquired, expires at %s", self._expires_at)

    async def ensure_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._token_valid:
            return self._access_token

        async with self._lock:
            if self._token_valid:
                return self._access_token
            await self._fetch_token()
            return self._access_token

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> dict:
        """Send a chat completion request to GigaChat.

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum tokens in response.

        Returns:
            The full API response dict (OpenAI-compatible format).
        """
        token = await self.ensure_token()

        async with httpx.AsyncClient(verify=self._verify, timeout=60.0) as client:
            resp = await client.post(
                f"{self._api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Convenience: send a single prompt and get the text reply."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = await self.chat_completion(messages)
        return data["choices"][0]["message"]["content"]


# Singleton
gigachat = GigaChatClient()
