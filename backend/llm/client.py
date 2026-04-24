"""
LLM provider abstraction for Niv AI.
Groq = primary (agents 1-5). Gemini = fallback (agent 6).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from groq import AsyncGroq, RateLimitError, APITimeoutError, APIConnectionError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


class LLMClient:
    def __init__(self) -> None:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY environment variable is required")
        self._groq = AsyncGroq(api_key=groq_key)
        self._gemini_model = None
        if _GEMINI_AVAILABLE:
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self._gemini_model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("Gemini configured as fallback")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15),
           retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
           reraise=True)
    async def _call_groq(self, system_prompt: str, user_message: str,
                         json_mode: bool = False, max_tokens: int = 3000) -> str:
        response = await self._groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_message}],
            temperature=0.1,
            response_format={"type": "json_object"} if json_mode else None,
            max_tokens=max_tokens)
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Groq returned empty response")
        return content

    async def _call_gemini(self, system_prompt: str, user_message: str) -> Optional[str]:
        if self._gemini_model is None:
            return None
        try:
            response = self._gemini_model.generate_content(
                f"{system_prompt}\n\n{user_message}",
                generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=4000))
            return response.text if response.text else None
        except Exception as e:
            logger.warning("Gemini failed (%s), falling back to Groq", e)
            return None

    async def run_agent(self, system_prompt: str, user_message: str, max_tokens: int = 3000) -> str:
        return await self._call_groq(system_prompt, user_message, json_mode=True, max_tokens=max_tokens)

    async def run_final_agent(self, system_prompt: str, user_message: str) -> str:
        gemini_result = await self._call_gemini(system_prompt, user_message)
        if gemini_result:
            return gemini_result
        return await self._call_groq(system_prompt, user_message, json_mode=True, max_tokens=4000)

    @staticmethod
    def parse_json(raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON: %s...", cleaned[:200])
            return {"error": "Failed to parse agent response", "raw": cleaned[:500]}
