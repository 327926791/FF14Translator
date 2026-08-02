from __future__ import annotations

from typing import List, Optional, Tuple

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

    def translate(
        self,
        speaker: str,
        text: str,
        protected_note: Optional[str] = None,
        *,
        term_pairs: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        system = (
            "你是《最终幻想14》（Final Fantasy XIV / FF14）的官方本地化翻译。\n"
            "输入文本来自游戏内对话框截图的 OCR 识别结果，是英文游戏对白。\n"
            "你的任务：把这段英文对白翻译成简体中文。\n"
            "严格规则：\n"
            "- 必须输出简体中文，绝对不能原样返回英文，也不能中英混杂。\n"
            "- 使用《最终幻想14》国服/官方的译名与词库（人名、地名、职业、技能、种族等专有名词）。\n"
            "- 保留占位符（如 __TERM_001__）不翻译。\n"
            "- 保留说话人名字，不要翻译名字本身。\n"
            "- 只输出翻译后的中文对白正文，不要加引号、不要加解释、不要重复英文原文。\n"
            "- 译文自然流畅，符合中文游戏叙事语境。\n"
            "- 即使输入很短或像是残缺句子，也要尽力翻译成中文，不得返回英文。"
        )

        glossary_lines = self._format_glossary(term_pairs)
        if glossary_lines:
            system += (
                "\n请使用以下 FF14 官方术语对照表（英文 => 中文），"
                "遇到这些词必须使用给定译名：\n" + glossary_lines
            )
        if protected_note:
            system += f"\n术语注记：\n{protected_note}"

        prompt = f"说话人：{speaker}\n英文对白：{text}" if speaker else f"英文对白：{text}"

        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 256,
            # 关闭 Qwen3 思维链推理：翻译无需推理，开启会大幅拖慢速度并浪费 token。
            # DashScope OpenAI 兼容接口下用 enable_thinking=false 关闭。
            "enable_thinking": False,
        }

        try:
            with httpx.Client(timeout=self.cfg.timeout_s) as client:
                result = self._request_content(client, url, headers, payload)
                # 兜底：若模型仍返回英文（无中文字符），追加强制指令重试一次。
                if result and not self._has_chinese(result):
                    retry_messages = messages + [
                        {"role": "assistant", "content": result},
                        {
                            "role": "user",
                            "content": (
                                "上面的回复仍然是英文。请只输出这段对白的简体中文翻译，"
                                "不要包含任何英文，不要解释。"
                            ),
                        },
                    ]
                    retry_payload = dict(payload)
                    retry_payload["messages"] = retry_messages
                    retried = self._request_content(client, url, headers, retry_payload)
                    if retried and self._has_chinese(retried):
                        return retried
                return result
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

    @staticmethod
    def _request_content(client: httpx.Client, url: str, headers: dict, payload: dict) -> str:
        """发起一次 chat/completions 请求并返回 message content。"""
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""

    @staticmethod
    def _has_chinese(text: str) -> bool:
        """判断文本是否包含中文字符（用于检测模型是否真的翻译了）。"""
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    @staticmethod
    def _format_glossary(term_pairs: Optional[List[Tuple[str, str]]]) -> str:
        """将 (英文, 中文) 词对整理为提示词里的术语对照行。

        - src == tgt：表示是需保留原文的专有名词。
        - 最多取 40 条，避免提示词过长增加成本。
        """
        if not term_pairs:
            return ""
        lines: List[str] = []
        for src, tgt in term_pairs:
            if not src:
                continue
            if tgt and tgt != src:
                lines.append(f"- {src} => {tgt}")
            else:
                lines.append(f"- {src} =>（保留原文 {src}）")
            if len(lines) >= 40:
                break
        return "\n".join(lines)

    def health_check(self) -> bool:
        """检查百炼 API 是否可用（用一次最小请求验证，消耗极少 token）。
        失败时抛出 RuntimeError，消息即为具体原因。
        """
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 1,
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
