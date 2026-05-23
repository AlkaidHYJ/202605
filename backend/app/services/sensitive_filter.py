"""基于 DFA 的敏感词过滤引擎"""
import re
from dataclasses import dataclass


@dataclass
class SensitiveHit:
    word: str
    level: int
    start: int
    end: int


class SensitiveWordEngine:
    def __init__(self):
        self._root: dict = {}
        self._patterns: list[tuple[re.Pattern, int, str]] = []

    def build(self, words: list[tuple[str, int, str | None]]):
        self._root = {}
        self._patterns = []
        for word, level, _ in words:
            if word.startswith("regex:"):
                pattern = re.compile(word[6:], re.IGNORECASE)
                self._patterns.append((pattern, level, word))
            else:
                self._add_word(word.lower(), level)

    def _add_word(self, word: str, level: int):
        node = self._root
        for char in word:
            node = node.setdefault(char, {})
        node["$"] = level

    def scan(self, text: str) -> list[SensitiveHit]:
        hits: list[SensitiveHit] = []
        lower = text.lower()
        length = len(lower)
        i = 0
        while i < length:
            node = self._root
            j = i
            last_level = None
            last_end = i
            while j < length and lower[j] in node:
                node = node[lower[j]]
                j += 1
                if "$" in node:
                    last_level = node["$"]
                    last_end = j
            if last_level is not None:
                hits.append(
                    SensitiveHit(
                        word=text[i:last_end],
                        level=last_level,
                        start=i,
                        end=last_end,
                    )
                )
                i = last_end
            else:
                i += 1

        for pattern, level, label in self._patterns:
            for match in pattern.finditer(text):
                hits.append(
                    SensitiveHit(
                        word=label,
                        level=level,
                        start=match.start(),
                        end=match.end(),
                    )
                )
        return hits

    def max_level(self, text: str) -> SensitiveHit | None:
        hits = self.scan(text)
        if not hits:
            return None
        return min(hits, key=lambda h: h.level)


engine = SensitiveWordEngine()
