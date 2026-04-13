from __future__ import annotations

import re
from collections.abc import Callable, Sequence

MODE_BUGFIX = "bugfix"
MODE_REFACTOR = "refactor"
MODE_FEATURE = "feature"
MODE_NEW_PROJECT = "new_project"

_BUGFIX_KEYWORDS: tuple[str, ...] = (
    "bugfix",
    "修复",
    "修復",
    "修bug",
    "补丁",
    "補丁",
    "报错",
    "報錯",
    "错误",
    "錯誤",
    "缺陷",
    "故障",
    "异常",
)

_REFACTOR_KEYWORDS: tuple[str, ...] = (
    "refactor",
    "重构",
    "重構",
    "重整",
    "整理代码",
    "代码整理",
    "代码清理",
    "清理代码",
    "cleanup",
    "重写",
    "重寫",
    "架构调整",
    "结构调整",
)

_FEATURE_KEYWORDS: tuple[str, ...] = (
    "feature",
    "功能",
    "新功能",
    "新增",
    "添加",
    "实现",
    "實現",
    "扩展",
    "擴展",
    "支持",
)

_ENGLISH_BUG_PATTERN = re.compile(r"\bbug\b", re.IGNORECASE)
_ENGLISH_FEATURE_PATTERN = re.compile(r"\bfeature\b", re.IGNORECASE)
_ENGLISH_REFACTOR_PATTERN = re.compile(r"\brefactor\b", re.IGNORECASE)

def _matches_bugfix(text: str) -> bool:
    normalized = text.casefold()
    return _contains_any(normalized, _BUGFIX_KEYWORDS) or _ENGLISH_BUG_PATTERN.search(text) is not None


def _matches_refactor(text: str) -> bool:
    normalized = text.casefold()
    return _contains_any(normalized, _REFACTOR_KEYWORDS) or _ENGLISH_REFACTOR_PATTERN.search(text) is not None


def _matches_feature(text: str) -> bool:
    normalized = text.casefold()
    return _contains_any(normalized, _FEATURE_KEYWORDS) or _ENGLISH_FEATURE_PATTERN.search(text) is not None


_MODE_MATCHERS: tuple[tuple[str, Callable[[str], bool]], ...] = (
    (MODE_BUGFIX, _matches_bugfix),
    (MODE_REFACTOR, _matches_refactor),
    (MODE_FEATURE, _matches_feature),
)


def classify_mode(text: str) -> str:
    """Classify text as bugfix/refactor/feature, or default to new_project.

    Priority is bugfix > refactor > feature > new_project.
    """
    for mode, matcher in _MODE_MATCHERS:
        if matcher(text):
            return mode

    return MODE_NEW_PROJECT


def _contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword in text for keyword in keywords)
