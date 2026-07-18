"""Formatting helpers for turning Issue lists into human/machine output."""

import json
from typing import List

from .models import Issue, Severity


def to_text(issues: List[Issue]) -> str:
    if not issues:
        return "No issues found."
    lines = [str(issue) for issue in issues]
    counts = summarize(issues)
    lines.append("")
    lines.append(
        f"Total: {len(issues)}  "
        f"(errors={counts['error']}, warnings={counts['warning']}, info={counts['info']})"
    )
    return "\n".join(lines)


def to_json(issues: List[Issue]) -> str:
    return json.dumps([issue.to_dict() for issue in issues], indent=2)


def summarize(issues: List[Issue]) -> dict:
    counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        counts[issue.severity.value] += 1
    return counts


def filter_by_severity(issues: List[Issue], min_severity: Severity) -> List[Issue]:
    return [i for i in issues if i.severity.rank() >= min_severity.rank()]
