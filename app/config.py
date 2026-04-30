from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import platformdirs
from pydantic import BaseModel, Field, ConfigDict

from app.translate.base import TranslatorType


class OllamaConfigModel(BaseModel):
    """Ollama 配置（Pydantic 模型）"""
    model_config = ConfigDict(use_attribute_docstrings=True)
    
    type: str = Field(default="ollama", description="翻译器类型")
    base_url: str = Field(default="http://localhost:11434", description="Ollama 服务地址")
    model: str = Field(default="qwen2.5:7b-instruct-q4_K_M", description="模型名称")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class DeepSeekConfigModel(BaseModel):
    """DeepSeek API 配置"""
    model_config = ConfigDict(use_attribute_docstrings=True)
    
    type: str = Field(default="deepseek", description="翻译器类型")
    api_key: str = Field(default="", description="API 密钥")
    base_url: str = Field(default="https://api.deepseek.com/v1", description="API 地址")
    model: str = Field(default="deepseek-chat", description="模型名称")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class QwenConfigModel(BaseModel):
    """通义千问通用聊天模型配置"""
    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str = Field(default="qwen", description="翻译器类型")
    api_key: str = Field(default="", description="API Key")
    base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        description="API 地址（见选项卡说明选对应区域）",
    )
    model: str = Field(default="qwen-flash", description="模型名称")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class QwenMtConfigModel(BaseModel):
    """Qwen-MT 专用翻译模型配置（qwen-mt-flash / qwen-mt-plus）"""
    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str = Field(default="qwen_mt", description="翻译器类型")
    api_key: str = Field(default="", description="API Key（与通义千问共用同一个）")
    base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        description="API 地址（Singapore / 国内 / 香港 可用 Qwen-MT）",
    )
    model: str = Field(default="qwen-mt-flash", description="模型（qwen-mt-flash 推荐）")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class QwenMtConfigModel(BaseModel):
    """Qwen-MT 专用翻译模型配置（qwen-mt-flash / qwen-mt-plus）"""
    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str = Field(default="qwen_mt", description="翻译器类型")
    api_key: str = Field(default="", description="API Key（与通义千问共用同一个）")
    base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        description="API 地址（国际站用 dashscope-intl，国内站用 dashscope）",
    )
    model: str = Field(default="qwen-mt-flash", description="模型（qwen-mt-flash 推荐）")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class BaiduConfigModel(BaseModel):
    """百度翻译 API 配置"""
    model_config = ConfigDict(use_attribute_docstrings=True)
    
    type: str = Field(default="baidu", description="翻译器类型")
    app_id: str = Field(default="", description="APP ID")
    secret_key: str = Field(default="", description="密钥")
    timeout_s: float = Field(default=30.0, description="超时时间（秒）")


class AppConfig(BaseModel):
    """应用全局配置"""
    model_config = ConfigDict(use_attribute_docstrings=True)
    
    # UI 配置
    window_width: int = Field(default=1100, description="窗口宽度")
    window_height: int = Field(default=700, description="窗口高度")
    
    # 捕获配置
    default_fps: int = Field(default=3, description="默认 FPS（帧率）", ge=1, le=10)
    default_ocr_interval_ms: int = Field(default=750, description="默认 OCR 间隔（毫秒）", ge=250, le=5000)
    
    # 翻译配置
    translator_type: str = Field(default="offline", description="翻译器类型（ollama/deepseek/qwen/qwen_mt/baidu/offline）")
    ollama: OllamaConfigModel = Field(default_factory=OllamaConfigModel, description="Ollama 配置")
    deepseek: DeepSeekConfigModel = Field(default_factory=DeepSeekConfigModel, description="DeepSeek 配置")
    qwen: QwenConfigModel = Field(default_factory=QwenConfigModel, description="通义千问通用模型配置")
    qwen_mt: QwenMtConfigModel = Field(default_factory=QwenMtConfigModel, description="Qwen-MT 专用翻译模型配置")
    baidu: BaiduConfigModel = Field(default_factory=BaiduConfigModel, description="百度翻译配置")
    
    # 术语表目录
    glossary_dir: str = Field(default="glossary", description="术语表目录")
    
    # 日志配置
    enable_logging: bool = Field(default=True, description="启用日志")
    log_file: Optional[str] = Field(default=None, description="日志文件路径（None 表示不写入文件）")

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> AppConfig:
        """从文件加载配置"""
        if path is None:
            path = cls._get_default_config_path()
        
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except Exception as e:
                print(f"加载配置文件失败 {path}：{e}，使用默认配置")
        
        return cls()

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """保存配置到文件"""
        if path is None:
            path = self._get_default_config_path()
        
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode='python')
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"配置已保存到 {path}")

    @staticmethod
    def _get_default_config_path() -> Path:
        """获取默认配置文件路径"""
        config_dir = Path(platformdirs.user_config_dir("FFXIV-Translator", ""))
        return config_dir / "config.json"

    def get_glossary_path(self) -> Path:
        """获取术语表目录路径"""
        path = Path(self.glossary_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# 全局配置实例
_global_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = AppConfig.load_from_file()
    return _global_config


def set_config(cfg: AppConfig) -> None:
    """设置全局配置实例"""
    global _global_config
    _global_config = cfg
