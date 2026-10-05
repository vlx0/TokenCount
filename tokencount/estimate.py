"""Rough token estimate (not exact tiktoken)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"\S+", re.UNICODE)
_CYR = re.compile(r"[\u0400-\u04FF]")


@dataclass
class Estimate:
    tokens: int
    tokens_low: int
    tokens_high: int
    chars: int
    words: int
    cyr_share: float
    method: str


def estimate(text: str) -> Estimate:
    chars = len(text)
    words = len(_WORD_RE.findall(text))
    if chars == 0 or not text.strip():
        return Estimate(0, 0, 0, chars, words, 0.0, "пусто")

    cyr = len(_CYR.findall(text))
    letters = sum(1 for ch in text if ch.isalpha())
    cyr_share = (cyr / letters) if letters else 0.0

    # эвристика: EN ~4 симв/токен, RU плотнее ~2.5–3
    if cyr_share >= 0.55:
        per = 2.8
        method = "кириллица · ~2.8 симв/токен"
        word_factor = 1.7
    elif cyr_share >= 0.15:
        per = 3.3
        method = "смесь · ~3.3 симв/токен"
        word_factor = 1.5
    else:
        per = 4.0
        method = "латиница · ~4 симв/токен"
        word_factor = 1.3

    char_mid = max(1, int(round(chars / per)))
    by_words = int(round(words * word_factor)) if words else 0

    if by_words:
        mid = int(round((char_mid + by_words) / 2))
        # коридор включает границы ±15% от char_mid, ±15% от mid и by_words
        low = min(int(math.floor(char_mid * 0.85)), int(math.floor(mid * 0.85)), by_words)
        high = max(int(math.ceil(char_mid * 1.15)), int(math.ceil(mid * 1.15)), by_words)
    else:
        mid = char_mid
        low = int(math.floor(mid * 0.85))
        high = int(math.ceil(mid * 1.15))

    # гарантия: 1 <= low <= mid <= high (mid всегда внутри коридора,
    # коридор не начинается с 0 при ненулевой оценке)
    low = max(1, min(low, mid))
    high = max(high, mid)
    # коридор не должен схлопываться в точку — расширим на 1
    if low == high and mid >= 1:
        high = mid + 1

    return Estimate(
        tokens=mid,
        tokens_low=low,
        tokens_high=high,
        chars=chars,
        words=words,
        cyr_share=cyr_share,
        method=method,
    )
