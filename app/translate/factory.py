from __future__ import annotations

from typing import Optional

from app.translate.base import (
    BaseTranslator,
    TranslatorType,
    OllamaConfig,
    DeepSeekConfig,
    QwenConfig,
    QwenMtConfig,
    BaiduConfig,
    TranslatorConfig,
)
from app.translate.ollama import OllamaTranslator
from app.translate.deepseek import DeepSeekTranslator
from app.translate.qwen import QwenTranslator
from app.translate.qwen_mt import QwenMtTranslator
from app.translate.baidu import BaiduTranslator


class TranslatorFactory:
    """翻译器工厂 - 根据类型和配置创建对应的翻译器"""

    @staticmethod
    def create(cfg: TranslatorConfig) -> Optional[BaseTranslator]:
        """
        根据配置创建翻译器
        
        Args:
            cfg: 翻译器配置对象
            
        Returns:
            翻译器实例，如果配置错误或类型不支持则返回 None
        """
        try:
            if cfg.type == TranslatorType.OLLAMA:
                if not isinstance(cfg, OllamaConfig):
                    cfg = OllamaConfig(
                        base_url=getattr(cfg, 'base_url', 'http://localhost:11434'),
                        model=getattr(cfg, 'model', 'qwen2.5:7b-instruct-q4_K_M'),
                    )
                return OllamaTranslator(cfg)
            
            elif cfg.type == TranslatorType.DEEPSEEK:
                if not isinstance(cfg, DeepSeekConfig):
                    raise ValueError("DeepSeek translator requires DeepSeekConfig")
                return DeepSeekTranslator(cfg)

            elif cfg.type == TranslatorType.QWEN:
                if not isinstance(cfg, QwenConfig):
                    raise ValueError("Qwen translator requires QwenConfig")
                return QwenTranslator(cfg)

            elif cfg.type == TranslatorType.QWEN_MT:
                if not isinstance(cfg, QwenMtConfig):
                    raise ValueError("QwenMt translator requires QwenMtConfig")
                return QwenMtTranslator(cfg)

            elif cfg.type == TranslatorType.BAIDU:
                if not isinstance(cfg, BaiduConfig):
                    raise ValueError("Baidu translator requires BaiduConfig")
                return BaiduTranslator(cfg)
            
            elif cfg.type == TranslatorType.OFFLINE:
                # 离线模式：直接返回原文
                return None
            
            else:
                raise ValueError(f"Unknown translator type: {cfg.type}")
        except Exception as e:
            print(f"创建翻译器失败：{e}")
            return None

    @staticmethod
    def get_supported_types() -> list[str]:
        """获取所有支持的翻译器类型"""
        return [t.value for t in TranslatorType]
