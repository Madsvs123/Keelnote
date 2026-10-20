"""Render a product log as a Keep a Changelog style markdown document."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from collections.abc import Sequence

from .semver import parse as parse_version

KIND_ORDER = ("added", "changed", "fixed", "removed")
KIND_TITLES = {
    "added": "Added",
    "changed": "Changed",
    "fixed": "Fixed",
    "removed": "Removed",
}


@dataclass(frozen=True)
class Note:
    kind: str
    text: str
    breaking: bool = False


@dataclass(frozen=True)
class VersionBlock:
    label: str
    released_on: date | None
    notes: tuple[Note, ...] = ()
    yanked_on: date | None = None
    yank_reason: str = ""


def render_changelog(
    product_name: str,
    versions: Sequence[VersionBlock],
    unreleased: Sequence[Note],
    repository_url: str = "",
) -> str:
    safe_name = " ".join(product_name.split()) or "this project"
    ordered = sorted(versions, key=lambda block: parse_version(block.label), reverse=True)
    lines: list[str] = [
        "# Changelog",
        "",
        f"All notable changes to {safe_name} are recorded in this file.",
        "",
        "Version numbers follow semantic versioning. Each release groups work into added, changed, fixed, and removed.",
        "",
        "## [Unreleased]",
        "",
    ]
    lines.extend(_render_notes(unreleased, "Nothing is waiting in the unreleased bucket."))
    for block in ordered:
        stamp = block.released_on.isoformat() if block.released_on else "draft"
        heading = f"## [{block.label}] - {stamp}"
        if block.yanked_on:
            heading += " [YANKED]"
        lines.append(heading)
        lines.append("")
        if block.yanked_on:
            reason = " ".join(block.yank_reason.split()) or "No reason recorded."
            lines.append(f"Yanked on {block.yanked_on.isoformat()}: {reason}")
            lines.append("")
        lines.extend(_render_notes(block.notes, "No notes were recorded for this version."))
    lines.extend(_link_lines(repository_url, ordered))
    return "\n".join(lines).rstrip() + "\n"


def render_unreleased(product_name: str, notes: Sequence[Note]) -> str:
    """Preview only the notes that have not been cut into a version."""
    safe_name = " ".join(product_name.split()) or "this project"
    lines = [
        f"# Unreleased changes to {safe_name}",
        "",
        "These notes have not been cut into a version yet.",
        "",
        "## [Unreleased]",
        "",
    ]
    lines.extend(_render_notes(notes, "Nothing is waiting in the unreleased bucket."))
    return "\n".join(lines).rstrip() + "\n"


def _render_notes(notes: Sequence[Note], empty: str) -> list[str]:
    buckets: dict[str, list[Note]] = {kind: [] for kind in KIND_ORDER}
    for note in notes:
        if note.kind not in buckets:
            raise ValueError(f"Unknown changelog kind: {note.kind}")
        text = note.text.strip()
        if text:
            buckets[note.kind].append(Note(note.kind, text, note.breaking))
    if not any(buckets.values()):
        return [f"_{empty}_", ""]
    lines: list[str] = []
    for kind in KIND_ORDER:
        items = buckets[kind]
        if not items:
            continue
        lines.append(f"### {KIND_TITLES[kind]}")
        lines.append("")
        for note in items:
            text = f"**Breaking.** {note.text}" if note.breaking else note.text
            lines.extend(_bullet_lines(text))
        lines.append("")
    return lines


def _bullet_lines(text: str) -> list[str]:
    parts = text.splitlines() or [""]
    lines = [f"- {parts[0]}"]
    for extra in parts[1:]:
        lines.append(f"  {extra}" if extra else "  ")
    return lines


def _link_lines(repository_url: str, ordered: Sequence[VersionBlock]) -> list[str]:
    repo = repository_url.strip().rstrip("/")
    if not repo.startswith(("http://", "https://")):
        return []
    published = [block for block in ordered if block.released_on]
    if published:
        unreleased = f"[Unreleased]: {repo}/compare/v{published[0].label}...HEAD"
    else:
        unreleased = f"[Unreleased]: {repo}/commits/HEAD"
    links = [unreleased]
    links.extend(f"[{block.label}]: {repo}/releases/tag/v{block.label}" for block in ordered)
    return links
