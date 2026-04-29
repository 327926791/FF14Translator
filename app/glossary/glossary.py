from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


_TOKEN_FMT = "__TERM_{:03d}__"


@dataclass
class Glossary:
    names: List[str]
    places: List[str]
    terms: List[str]

    @classmethod
    def load_from_dir(cls, folder: Path) -> "Glossary":
        def read_list(p: Path) -> List[str]:
            if not p.exists():
                return []
            items: List[str] = []
            for line in p.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                items.append(s)
            # 长词优先，避免短词把长词切碎
            items.sort(key=len, reverse=True)
            return items

        return cls(
            names=read_list(folder / "names.txt"),
            places=read_list(folder / "places.txt"),
            terms=read_list(folder / "terms.txt"),
        )

    def all_terms(self) -> List[str]:
        # names/places/terms 都视为“不要翻译”
        merged = list(dict.fromkeys(self.names + self.places + self.terms))
        merged.sort(key=len, reverse=True)
        return merged


def protect_terms(text: str, terms: List[str]) -> Tuple[str, Dict[str, str]]:
    """
    将 terms 中出现的片段替换为占位符，返回 (protected_text, mapping)。
    """
    mapping: Dict[str, str] = {}
    if not terms or not text:
        return text, mapping

    out = text
    idx = 1
    for term in terms:
        if not term or term not in out:
            continue
        token = _TOKEN_FMT.format(idx)
        idx += 1
        mapping[token] = term
        out = out.replace(term, token)
    return out, mapping


_TOKEN_RE = re.compile(r"__TERM_\d{3}__")


def restore_terms(text: str, mapping: Dict[str, str]) -> str:
    if not mapping or not text:
        return text

    def repl(m: re.Match) -> str:
        tok = m.group(0)
        return mapping.get(tok, tok)

    return _TOKEN_RE.sub(repl, text)

