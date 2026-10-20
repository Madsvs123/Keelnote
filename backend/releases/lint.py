"""Check changelog notes for a missing kind or an empty summary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .markdown import KIND_ORDER


@dataclass(frozen=True)
class LintIssue:
    code: str
    message: str
    index: int
    entry_id: int | None = None

    def as_dict(self) -> dict:
        payload = {
            "code": self.code,
            "message": self.message,
            "index": self.index,
        }
        if self.entry_id is not None:
            payload["entry"] = self.entry_id
        return payload


def lint_notes(notes: Sequence[Mapping]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    allowed = set(KIND_ORDER)
    for index, note in enumerate(notes):
        raw_kind = note.get("kind")
        kind = raw_kind.strip() if isinstance(raw_kind, str) else ""
        raw_text = note.get("text", note.get("summary", ""))
        text = raw_text.strip() if isinstance(raw_text, str) else ""
        entry_id = note.get("id")
        if not isinstance(entry_id, int):
            entry_id = None
        if kind not in allowed:
            issues.append(
                LintIssue(
                    "missing_kind",
                    "Every note needs a kind: added, changed, fixed, or removed.",
                    index,
                    entry_id,
                )
            )
        if not text:
            issues.append(
                LintIssue(
                    "empty_summary",
                    "Write a summary before this note can ship.",
                    index,
                    entry_id,
                )
            )
    return issues
