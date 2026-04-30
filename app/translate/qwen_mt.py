from __future__ import annotations

from typing import List, Optional, Tuple

import httpx

from app.translate.base import BaseTranslator, QwenMtConfig


class QwenMtTranslator(BaseTranslator):
    """
    Qwen-MT 专用翻译模型翻译器。

    使用阿里云百炼平台的 Qwen-MT 系列模型（qwen-mt-flash / qwen-mt-plus）。
    相比通用 Qwen 聊天模型，翻译质量更高、成本更低，专为翻译任务 fine-tune。

    API 特点：
    - 通过 translation_options.source_lang / target_lang 指定语言对
    - 支持 translation_options.terms 列表指定"不翻译"的词条
    - 不支持 system message；messages 仅含 user 角色

    官方文档：https://alibabacloud.com/help/en/model-studio/translation-abilities
    """

    def __init__(self, cfg: QwenMtConfig) -> None:
        if not cfg.api_key:
            raise ValueError("Qwen-MT API key is required")
        self.cfg = cfg

    def translate(
        self,
        speaker: str,
        text: str,
        protected_note: Optional[str] = None,
        *,
        term_pairs: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        """
        调用 Qwen-MT API 翻译文本。

        Args:
            speaker: 说话人名称（上下文参考，不发给 API）
            text: 待翻译的英文文本
            protected_note: 保留参数，暂未使用
            term_pairs: (英文, 中文) 词对列表，传给 translation_options.terms
                        告知模型使用指定译名；若 source==target 则表示保留原文

        Returns:
            翻译后的中文文本
        """
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }

        translation_options: dict = {
            "source_lang": self.cfg.source_lang,
            "target_lang": self.cfg.target_lang,
        }
        if term_pairs:
            translation_options["terms"] = [
                {"source": src, "target": tgt}
                for src, tgt in term_pairs
                if src
            ]

        payload = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": text}],
            "translation_options": translation_options,
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
        """检查 API 是否可用（消耗极少 token）。失败时抛出 RuntimeError。"""
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
