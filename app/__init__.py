"""
FFXIV 实时翻译工具 v2.0

一个用于 FF14 过场/对白框英文台词实时翻译的 Windows 应用。

特性：
- 屏幕 ROI 截图和 OCR 识别
- 支持多种翻译后端（Ollama/DeepSeek/百度/离线）
- 术语保护（人名/地名不翻译）
- 配置持久化
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__license__ = "MIT"

# 导出主要模块
from app.config import AppConfig, get_config, set_config
from app.translate.base import BaseTranslator, TranslatorType
from app.translate.factory import TranslatorFactory

__all__ = [
    "AppConfig",
    "get_config",
    "set_config",
    "BaseTranslator",
    "TranslatorType",
    "TranslatorFactory",
]
