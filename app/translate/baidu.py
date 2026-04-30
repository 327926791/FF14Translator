from __future__ import annotations

import hashlib
import random
from typing import Optional

import httpx

from app.translate.base import BaseTranslator, BaiduConfig


class BaiduTranslator(BaseTranslator):
    """
    百度翻译 API 翻译器
    
    使用百度翻译的通用翻译 API。
    
    获取凭证：https://api.fanyi.baidu.com
    免费额度：每月 2M 字符
    """

    def __init__(self, cfg: BaiduConfig) -> None:
        if not cfg.app_id or not cfg.secret_key:
            raise ValueError("Baidu app_id and secret_key are required")
        self.cfg = cfg

    def _gen_sign(self, query: str, salt: int) -> str:
        """生成百度翻译 sign：MD5(appid + q + salt + secret_key)"""
        sign_str = f"{self.cfg.app_id}{query}{salt}{self.cfg.secret_key}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def translate(self, speaker: str, text: str, protected_note: Optional[str] = None) -> str:
        """调用百度翻译 API。

        百度通用翻译 API 不支持系统 prompt，所以直接翻译保护后的文本。
        __TERM_XXX__ 占位符会被翻译成乱码，因此对百度后端跳过术语保护，
        由调用层在收到结果后再做中文→原文的二次替换（见 worker.py）。
        """
        query = text
        salt = random.randint(32768, 65536)
        sign = self._gen_sign(query, salt)
        
        url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
        params = {
            "q": query,
            "from": "en",
            "to": "zh",
            "appid": self.cfg.app_id,
            "salt": salt,
            "sign": sign,
        }
        
        try:
            with httpx.Client(timeout=self.cfg.timeout_s) as client:
                r = client.post(url, data=params)
                r.raise_for_status()
                data = r.json()
                
                if data.get("error_code"):
                    raise RuntimeError(f"百度翻译错误：{data.get('error_msg', 'Unknown')}")
                
                trans_result = data.get("trans_result", [])
                if trans_result and len(trans_result) > 0:
                    return trans_result[0].get("dst", "").strip()
                return ""
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"百度翻译 HTTP 错误：{e.response.status_code}") from e
        except Exception as e:
            raise RuntimeError(f"百度翻译失败：{str(e)}") from e

    def health_check(self) -> bool:
        """检查百度翻译 API 是否可用"""
        try:
            query = "test"
            salt = random.randint(32768, 65536)
            sign = self._gen_sign(query, salt)
            
            url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
            params = {
                "q": query,
                "from": "en",
                "to": "zh",
                "appid": self.cfg.app_id,
                "salt": salt,
                "sign": sign,
            }
            
            with httpx.Client(timeout=5.0) as client:
                r = client.post(url, data=params)
                r.raise_for_status()
                data = r.json()
                return not data.get("error_code")
        except Exception:
            return False
