from __future__ import annotations

from typing import Optional

import httpx

from app.translate.base import BaseTranslator, QwenMtConfig


class QwenMtTranslator(BaseTranslator):
    """
    Qwen-MT 专用翻译模型翻译器。

    使用阿里云百炼平台的 Qwen-MT 系列模型（qwen-mt-flash / qwen-mt-plus）。
    相比通用 Qwen 聊天模型，翻译质量更高、成本更低，专为翻译任务 fine-tune。

    API 特点：
    - 通过 extra_body.translation_options 指定语言对
    - 不支持 system message
    - messages 仅含 user 角色，content 即待翻译文本

    官方文档：https://alibabacloud.com/help/en/model-studio/translation-abilities
    获取免费 API Key：https://bailian.console.aliyun.com/
    """

    def __init__(self, cfg: QwenMtConfig) -> None:
        if not cfg.api_key:
            raise ValueError("Qwen-MT API key is required")
        self.cfg = cfg

    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        """
        调用 Qwen-MT API 翻译文本。

        Qwen-MT 不支持 system prompt，无法使用占位符保护术语。
        发送的是原始文本，由模型自行处理专有名词。
        """
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": text}],
            "translation_options": {
                "source_lang": self.cfg.source_lang,
                "target_lang": self.cfg.target_lang,
            },
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
            raise RuntimeError(f"Qwen-MT API 错误：{error_detail}") from e
        except Exception as e:
            raise RuntimeError(f"Qwen-MT 翻译失败：{str(e)}") from e

    def health_check(self) -> bool:
        """检查百炼 MT API 是否可用（翻译一个单词验证，消耗极少 token）。
        失败时抛出 RuntimeError，消息即为具体原因。
        """
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": "test"}],
            "translation_options": {
                "source_lang": self.cfg.source_lang,
                "target_lang": self.cfg.target_lang,
            },
            "max_tokens": 4,
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            detail = f"HTTP {e.response.status_code}"
            try:
                detail = e.response.json().get("error", {}).get("message", detail)
            except Exception:
                pass
            raise RuntimeError(f"API 返回错误：{detail}") from e
        except httpx.ConnectError as e:
            raise RuntimeError(f"无法连接到服务器，请检查网络或 API 地址：{e}") from e
        except Exception as e:
            raise RuntimeError(f"连接检查失败：{e}") from e
