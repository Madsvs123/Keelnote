"""Starter wording for a changelog note.

Built-in templates are shared. A maintainer can also save their own.
"""

from __future__ import annotations

BUILT_IN_TEMPLATES = (
    {
        "slug": "added-behavior",
        "name": "Added behavior",
        "kind": "added",
        "body": "Add {behavior} so that {who} can {outcome}.",
    },
    {
        "slug": "changed-behavior",
        "name": "Changed behavior",
        "kind": "changed",
        "body": "Change {behavior}. Previously {before}.",
    },
    {
        "slug": "fixed-defect",
        "name": "Fixed defect",
        "kind": "fixed",
        "body": "Fix {defect} that caused {symptom}.",
    },
    {
        "slug": "removed-behavior",
        "name": "Removed behavior",
        "kind": "removed",
        "body": "Remove {behavior}. Use {replacement} instead.",
    },
)


def built_in_payload() -> list[dict]:
    return [
        {
            "id": None,
            "slug": item["slug"],
            "name": item["name"],
            "kind": item["kind"],
            "body": item["body"],
            "builtin": True,
        }
        for item in BUILT_IN_TEMPLATES
    ]
