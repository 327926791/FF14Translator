from __future__ import annotations

from typing import Optional

import httpx

from app.translate.base import BaseTranslator, QwenConfig


class QwenTranslator(BaseTranslator):
    """
    通义千问（阿里云百炼）API 翻译器。

    使用 OpenAI 兼容接口，与 DeepSeek 接口格式完全相同。

    获取免费 API Key（新用户 100 万 Token）：
        https://bailian.console.aliyun.com/
    推荐模型：qwen-turbo（速度快、成本最低）
    """

    def __init__(self, cfg: QwenConfig) -> None:
        if not cfg.api_key:
            raise ValueError("Qwen API key is required")
        self.cfg = cfg

    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        system = (
            "你是一名专业翻译，负责将《最终幻想XIV》英文对白翻译成简体中文。\n"
            "规则：\n"
            "- 保留占位符（如 __TERM_001__）不翻译。\n"
            "- 保留说话人名字不翻译。\n"
            "- 只输出翻译后的中文对白，不加引号、不加解释。\n"
            "- 语言自然流畅，符合中文游戏语境。"
        )
        if protected_note:
            system += f"\n术语注记：\n{protected_note}"

        prompt = f"说话人：{speaker}\n对白：{text}" if speaker else f"对白：{text}"

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
            "max_tokens": 256,
        }

        try:
            with httpx.Client(timeout=self.cfg.timeout_s) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                err_data = e.response.json()
                error_detail = err_data.get("error", {}).get("message", error_detail)
            except Exception:
                pass
            raise RuntimeError(f"Qwen API 错误：{error_detail}") from e
        except Exception as e:
            raise RuntimeError(f"Qwen 翻译失败：{str(e)}") from e

    def health_check(self) -> bool:
        """检查百炼 API 是否可用"""
        try:
            url = self.cfg.base_url.rstrip("/") + "/models"
            headers = {"Authorization": f"Bearer {self.cfg.api_key}"}
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url, headers=headers)
                r.raise_for_status()
                return True
        except Exception:
            return False
