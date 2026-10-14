from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass
class GeminiResult:
    raw_text: str
    parsed: dict[str, Any] | None


class GeminiService:
    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-3.6-flash"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def vision_configured(self) -> bool:
        return self.configured or bool(getattr(settings, "OPENAI_API_KEY", ""))

    def generate_json(self, *, prompt: str, schema: dict[str, Any] | None = None, timeout: int = 25) -> dict[str, Any] | None:
        if not self.configured:
            return None
        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.6,
            },
        }
        if schema:
            payload["generationConfig"]["responseSchema"] = schema

        result = self._post_json(payload, timeout=timeout)
        return result.parsed

    def recognize_ingredients_from_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        timeout: int = 30,
    ) -> dict[str, Any] | None:
        if not self.vision_configured:
            return None

        prompt = (
            "You are SmartChef Vision. Identify the visible ingredient(s) in this image. "
            "Return only valid JSON with the schema "
            '{"ingredients":[{"name":"","confidence":0.0}],"confidence":0.0,"is_food":true}. '
            "Return up to 5 distinct ingredients ordered by confidence."
        )

        if not self.configured:
            return self._openai_vision(image_bytes=image_bytes, mime_type=mime_type, timeout=timeout)
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
        result = self._post_json(payload, timeout=timeout)
        return result.parsed

    def _openai_vision(self, *, image_bytes: bytes, mime_type: str, timeout: int) -> dict[str, Any] | None:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        prompt = ('Identify all visible food ingredients. Return only JSON in this format: '
                  '{"ingredients":[{"name":"","confidence":0.0}],"confidence":0.0,"is_food":true}. '
                  'Use a specific ingredient name and never invent an ingredient.')
        payload = {"model": getattr(settings, "OPENAI_VISION_MODEL", "gpt-4o-mini"), "temperature": 0.1,
                   "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": [
                       {"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"}}
                   ]}]}
        request = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                decoded = json.loads(response.read().decode())
            content = decoded["choices"][0]["message"]["content"]
            return self._safe_json(content)
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, IndexError, TypeError, ValueError):
            return None

    def recognize_nutrition_scan(self, *, image_bytes: bytes, mime_type: str, timeout: int = 45) -> dict[str, Any] | None:
        if not self.configured:
            return None
        prompt = ('Read the digital weighing scale display in this image. Return only JSON: '
                  '{"ingredient":"", "weight_grams":0, "confidence":0}. '
                  'The image may show only the lower scale area, so read the bright numeric display exactly. '
                  'Return the number shown in grams; do not estimate a portion weight. '
                  'Leave ingredient empty if it is not visible.')
        payload = {"contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}}]}],
                   "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}}
        return self._post_json(payload, timeout=timeout).parsed

    def _post_json(self, payload: dict[str, Any], *, timeout: int) -> GeminiResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            raise RuntimeError(f"Gemini HTTP {exc.code}: {body[:300]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

        raw_text = self._extract_text(response_text)
        parsed = self._safe_json(raw_text)
        return GeminiResult(raw_text=raw_text, parsed=parsed)

    def _extract_text(self, response_text: str) -> str:
        try:
            decoded = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON payload.") from exc

        candidates = decoded.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise RuntimeError("Gemini response did not contain text content.")

    def _safe_json(self, raw_text: str) -> dict[str, Any] | None:
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            decoded = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None


class ExternalAIService(GeminiService):
    def is_configured(self) -> bool:
        return self.configured
