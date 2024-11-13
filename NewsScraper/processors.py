from typing import Any

from NewsScraper.utils import normalize_whitespaces


class TakeFirstNonZero:
    def __call__(self, values: Any) -> Any:
        for value in values:
            _value = normalize_whitespaces(value)
            if _value and _value != '0':
                return _value


class JoinNonEmpty:
    def __init__(self, separator=" "):
        self.separator = separator

    def __call__(self, values):
        return self.separator.join([v.strip() for v in values if v and v.strip()])


class JoinUniqueNonEmpty:
    def __init__(self, separator=" "):
        self.separator = separator

    def __call__(self, values):
        return self.separator.join(list(dict.fromkeys([v.strip() for v in values if v and v.strip()])))
