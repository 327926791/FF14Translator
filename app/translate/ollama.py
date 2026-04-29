from __future__ import annotations

from typing import Optional

import httpx

from app.translate.base import BaseTranslator, OllamaConfig


class OllamaTranslator(BaseTranslator):
    def __init__(self, cfg: OllamaConfig) -> None:
        self.cfg = cfg

    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        system = (
            "You are a translator. Translate the dialogue into Simplified Chinese.\n"
            "Rules:\n"
            "- Keep placeholders like __TERM_001__ unchanged.\n"
            "- Keep speaker name unchanged.\n"
            "- Keep proper nouns unchanged if they appear as placeholders.\n"
            "- Output ONLY the translated Chinese dialogue content, no quotes, no explanations."
        )
        if protected_note:
            system += f"\nGlossary note:\n{protected_note}"

        prompt = f"Speaker: {speaker}\nDialogue: {text}"
        url = self.cfg.base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.cfg.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        with httpx.Client(timeout=self.cfg.timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            # Ollama: { message: { content: "..." } }
            return (data.get("message", {}) or {}).get("content", "").strip()

    def health_check(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            url = self.cfg.base_url.rstrip("/") + "/api/tags"
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url)
                r.raise_for_status()
                data = r.json()
                # 检查是否有可用模型
                models = data.get("models", [])
                return len(models) > 0
        except Exception:
            return False

