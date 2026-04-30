from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TranslatorType(str, Enum):
    """翻译后端类型枚举"""
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    QWEN_MT = "qwen_mt"  # 专用翻译模型（qwen-mt-flash / qwen-mt-plus）
    BAIDU = "baidu"
    OFFLINE = "offline"  # 离线模式（暂不翻译）


@dataclass(frozen=True)
class TranslatorConfig:
    """翻译器配置基类"""
    type: TranslatorType
    timeout_s: float = 30.0


@dataclass(frozen=True)
class OllamaConfig(TranslatorConfig):
    """本地 Ollama 配置"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b-instruct-q4_K_M"
    type: TranslatorType = TranslatorType.OLLAMA


@dataclass(frozen=True)
class DeepSeekConfig(TranslatorConfig):
    """DeepSeek API 配置"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    type: TranslatorType = TranslatorType.DEEPSEEK


@dataclass(frozen=True)
class QwenConfig(TranslatorConfig):
    """通义千问通用聊天模型配置（qwen-flash / qwen-plus / qwen-max 等）"""
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-flash"  # qwen-turbo 已停止更新，官方推荐 qwen-flash
    type: TranslatorType = TranslatorType.QWEN


@dataclass(frozen=True)
class QwenMtConfig(TranslatorConfig):
    """Qwen-MT 专用翻译模型配置（qwen-mt-flash / qwen-mt-plus）

    特点：专为翻译场景 fine-tune，比通用聊天模型质量更高，且更便宜。
    注意：不支持 system message，通过 translation_options 指定语言。
    """
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-mt-flash"
    source_lang: str = "en"
    target_lang: str = "zh"
    type: TranslatorType = TranslatorType.QWEN_MT


@dataclass(frozen=True)
class BaiduConfig(TranslatorConfig):
    """百度翻译 API 配置"""
    app_id: str = ""
    secret_key: str = ""
    type: TranslatorType = TranslatorType.BAIDU


class BaseTranslator(ABC):
    """翻译器基类"""

    @abstractmethod
    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        """
        翻译文本
        
        Args:
            speaker: 说话人名字
            text: 要翻译的文本（已保护术语）
            protected_note: 术语保护注记（可选）
            
        Returns:
            翻译后的中文文本
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """检查翻译服务是否可用"""
        pass
