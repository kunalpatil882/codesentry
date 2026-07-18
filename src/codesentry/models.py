"""Shared data structures for CodeSentry."""

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    def rank(self) -> int:
        return {"info": 0, "warning": 1, "error": 2}[self.value]


@dataclass(frozen=True)
class Issue:
    file: str
    line: int
    rule_id: str
    severity: Severity
    message: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: [{self.severity.value.upper()}] {self.rule_id} - {self.message}"
