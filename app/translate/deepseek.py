from __future__ import annotations

import json
from typing import Optional

import httpx

from app.translate.base import BaseTranslator, DeepSeekConfig


class DeepSeekTranslator(BaseTranslator):
    """
    DeepSeek API 翻译器
    
    使用 DeepSeek 的开放 API 进行翻译。
    
    获取 API 密钥：https://api.deepseek.com
    文档：https://api-docs.deepseek.com/zh-cn/
    """

    def __init__(self, cfg: DeepSeekConfig) -> None:
        if not cfg.api_key:
            raise ValueError("DeepSeek API key is required")
        self.cfg = cfg

    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        """调用 DeepSeek API 进行翻译"""
        system = (
            "You are a professional translator. Translate the dialogue into Simplified Chinese.\n"
            "Rules:\n"
            "- Keep placeholders like __TERM_001__ unchanged.\n"
            "- Keep speaker name unchanged.\n"
            "- Keep proper nouns unchanged if they appear as placeholders.\n"
            "- Output ONLY the translated Chinese dialogue, no quotes, no explanations.\n"
            "- Be concise and natural."
        )
        if protected_note:
            system += f"\nGlossary note:\n{protected_note}"

        prompt = f"Speaker: {speaker}\nDialogue: {text}"
        
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "top_p": 0.95,
            "max_tokens": 256,
        }

        try:
            with httpx.Client(timeout=self.cfg.timeout_s) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                # OpenAI-compatible format
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    msg = choices[0].get("message", {})
                    return msg.get("content", "").strip()
                return ""
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                err_data = e.response.json()
                error_detail = err_data.get("error", {}).get("message", error_detail)
            except Exception:
                pass
            raise RuntimeError(f"DeepSeek API 错误：{error_detail}") from e
        except Exception as e:
            raise RuntimeError(f"DeepSeek 翻译失败：{str(e)}") from e

    def health_check(self) -> bool:
        """检查 DeepSeek API 是否可用"""
        try:
            url = self.cfg.base_url.rstrip("/") + "/models"
            headers = {
                "Authorization": f"Bearer {self.cfg.api_key}",
            }
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url, headers=headers)
                r.raise_for_status()
                return True
        except Exception:
            return False
