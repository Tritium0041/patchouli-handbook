from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class ChatGateway(Protocol):
    def complete(self, messages: Sequence[dict[str, str]], *, json_mode: bool) -> str:
        raise NotImplementedError


class OpenAIChatGateway:
    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def complete(self, messages: Sequence[dict[str, str]], *, json_mode: bool) -> str:
        request_kwargs = {
            "model": self.model,
            "messages": list(messages),
            "temperature": 0.2,
        }
        if json_mode:
            request_kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(**request_kwargs)
        content = response.choices[0].message.content
        if isinstance(content, list):
            return "".join(
                part.text for part in content if getattr(part, "type", None) == "text"
            )
        return content or ""
