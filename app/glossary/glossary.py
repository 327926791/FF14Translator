from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


_TOKEN_FMT = "__TERM_{:03d}__"

# 句首或引号后常见的普通英文词，不当作专有名词
_COMMON_WORDS: frozenset[str] = frozenset({
    "I", "A", "An", "The", "It", "He", "She", "We", "You", "They",
    "Is", "Are", "Was", "Were", "Have", "Has", "Had", "Do", "Does", "Did",
    "Will", "Would", "Could", "Should", "May", "Might", "Can", "Must", "Shall",
    "Not", "No", "Yes", "And", "But", "Or", "For", "In", "On", "At", "To",
    "Of", "With", "As", "By", "From", "Into", "Through", "During", "Before",
    "After", "Up", "Down", "Out", "Off", "Over", "Under", "Then", "Now",
    "My", "Your", "His", "Her", "Its", "Our", "Their",
    "This", "That", "These", "Those",
    "What", "Which", "Who", "How", "When", "Where", "Why",
    "If", "So", "Here", "There", "Oh", "Ah", "Well", "Please",
    "Just", "Only", "Very", "More", "Most", "Some", "Any", "All",
    "Be", "Been", "Being", "Go", "Gone", "Come", "Back", "Get", "See",
    "Say", "Tell", "Know", "Think", "Make", "Take", "Give",
    "Need", "Want", "Let", "Try", "Too", "Even", "Still", "Also",
    "One", "Two", "Three", "First", "Last", "New", "Old", "Good", "Great",
    "Long", "True", "Right", "Sure", "Much", "Many",
})

# 允许出现在多词短语中间的连接词
_CONNECTORS: frozenset[str] = frozenset({"of", "the", "a", "an", "in", "at", "and", "or"})

_CAP_WORD = re.compile(r"[A-Z][A-Za-z''\-]*")


def _parse_term_line(line: str) -> Tuple[str, str] | None:
    """
    解析词库行。支持两种格式：
      - ``English Term = 官方中文`` → (english, chinese)
      - ``English Term``            → (english, english)  即保留原文
    忽略 # 开头的注释和空行。
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if "=" in s:
        en, _, zh = s.partition("=")
        en = en.strip()
        zh = zh.strip()
        if en and zh:
            return en, zh
    else:
        if s:
            return s, s   # 无翻译 → 保留原文
    return None


@dataclass
class Glossary:
    """
    词库。每条记录是 (英文原文, 目标译文) 对。
    若目标译文 == 英文原文，则表示该词保留不翻译。
    """
    # 内部存 {英文: 中文} 映射（长词优先）
    _pairs: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load_from_dir(cls, folder: Path) -> "Glossary":
        pairs: Dict[str, str] = {}
        for fname in ("names.txt", "places.txt", "terms.txt"):
            p = folder / fname
            if not p.exists():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                result = _parse_term_line(line)
                if result:
                    en, zh = result
                    pairs[en] = zh
        obj = cls()
        obj._pairs = pairs
        return obj

    def term_pairs(self) -> List[Tuple[str, str]]:
        """返回 (英文, 中文) 词对列表，按英文长度降序（长词优先）。"""
        return sorted(self._pairs.items(), key=lambda kv: -len(kv[0]))

    def all_terms(self) -> List[str]:
        """向后兼容：仅返回英文词列表（长词优先）。"""
        return sorted(self._pairs.keys(), key=len, reverse=True)


def detect_proper_nouns(text: str, known_terms: set[str] | None = None) -> List[str]:
    """
    从英文文本中自动检测尚未收录在词库里的专有名词（首字母大写词/短语）。
    返回列表用于告知翻译器"这些词保留原文"。

    - 跳过已在 known_terms 中的词（它们已有准确译名）
    - 跳过普通英文常用词
    - 支持带 apostrophe / hyphen 的名字（Y'shtola, Kan-E-Senna）
    - 尝试合并相邻大写词组成多词专有名词
    """
    if known_terms is None:
        known_terms = set()

    results: List[str] = []
    tokens = re.split(r"(\s+|[,.:;!?\"()\[\]{}])", text)
    clean = [w for w in tokens if w.strip() and not re.fullmatch(r"\s+", w)]

    i = 0
    while i < len(clean):
        raw = clean[i].strip(".,!?;:\"'()")
        if not raw or not _CAP_WORD.match(raw):
            i += 1
            continue
        if raw in _COMMON_WORDS:
            i += 1
            continue

        phrase_tokens = [raw]
        j = i + 1
        pending: List[str] = []

        while j < len(clean):
            nxt = clean[j].strip(".,!?;:\"'()")
            if not nxt:
                j += 1
                continue
            if nxt.lower() in _CONNECTORS:
                pending.append(nxt)
                j += 1
                continue
            if _CAP_WORD.match(nxt) and nxt not in _COMMON_WORDS:
                phrase_tokens.extend(pending)
                phrase_tokens.append(nxt)
                pending = []
                j += 1
            else:
                break

        phrase = " ".join(phrase_tokens)
        if phrase and phrase not in _COMMON_WORDS and phrase not in known_terms:
            results.append(phrase)
        i = j

    # 去重，长词优先
    seen: dict[str, int] = {}
    for p in results:
        if p not in seen:
            seen[p] = len(p)
    return sorted(seen.keys(), key=lambda x: -seen[x])


def protect_terms(text: str, terms: List[str]) -> Tuple[str, Dict[str, str]]:
    """将 terms 中出现的片段替换为占位符，返回 (protected_text, mapping)。"""
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
        return mapping.get(m.group(0), m.group(0))

    return _TOKEN_RE.sub(repl, text)
