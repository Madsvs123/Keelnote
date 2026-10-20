"""Release cuts, publishing, and changelog assembly."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from .markdown import Note, VersionBlock, render_changelog
from .models import ChangelogEntry, Product, Version
from .semver import CHANNELS, InvalidVersion, SemVer


class ReleaseError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def unique_slug(owner, name: str, exclude_pk: int | None = None) -> str:
    base = (slugify(name) or "product")[:120]
    candidate = base
    number = 2
    existing = Product.objects.filter(owner=owner)
    if exclude_pk is not None:
        existing = existing.exclude(pk=exclude_pk)
    while existing.filter(slug=candidate).exists():
        suffix = f"-{number}"
        candidate = f"{base[: 140 - len(suffix)]}{suffix}"
        number += 1
    return candidate


def greatest_version(product: Product) -> Version | None:
    versions = list(product.versions.all())
    if not versions:
        return None
    return max(versions, key=lambda version: version.as_semver())


def version_base(product: Product) -> tuple[Version | None, SemVer]:
    current = greatest_version(product)
    if current is None:
        return None, SemVer(0, 0, 0)
    return current, current.as_semver()


def normalize_prerelease(value: str) -> str:
    text = value.strip()
    if text.startswith("-"):
        text = text[1:].strip()
    if not text:
        return ""
    try:
        SemVer(0, 0, 0, text)
    except InvalidVersion as exc:
        raise ReleaseError(str(exc)) from exc
    return text


@transaction.atomic
def cut_release(product: Product, level: str, prerelease: str = "") -> Version:
    if level not in {"major", "minor", "patch", *CHANNELS}:
        raise ReleaseError("Choose major, minor, patch, alpha, beta, or rc.")
    locked = Product.objects.get(pk=product.pk)
    _current, base = version_base(locked)
    try:
        if level in CHANNELS:
            if prerelease.strip():
                raise ReleaseError("A channel bump sets its own pre-release label.")
            nxt = base.advance_channel(level)
        else:
            nxt = base.bump(level)
            pre = normalize_prerelease(prerelease)
            if pre:
                nxt = SemVer(nxt.major, nxt.minor, nxt.patch, pre)
    except InvalidVersion as exc:
        raise ReleaseError(str(exc)) from exc
    try:
        with transaction.atomic():
            version = Version.objects.create(
                product=locked,
                major=nxt.major,
                minor=nxt.minor,
                patch=nxt.patch,
                prerelease=nxt.prerelease,
            )
            ChangelogEntry.objects.filter(product=locked, version__isnull=True).update(version=version)
    except IntegrityError as exc:
        raise ReleaseError("That version already exists.", 409) from exc
    return version


def yank_version(version: Version, reason: str) -> Version:
    """Withdraw a published version and keep every note attached to it."""
    if version.released_on is None:
        raise ReleaseError("Only a published version can be yanked.")
    if version.yanked_on is not None:
        raise ReleaseError("This version is already yanked.", 409)
    cleaned = " ".join(reason.split())
    if len(cleaned) < 3:
        raise ReleaseError("Say why this version is yanked.")
    if len(cleaned) > 280:
        raise ReleaseError("Keep the yank reason under 280 characters.")
    version.yanked_on = timezone.localdate()
    version.yank_reason = cleaned
    version.save(update_fields=["yanked_on", "yank_reason"])
    return version


def publish_version(version: Version) -> Version:
    if version.released_on is not None:
        raise ReleaseError("This version is already published.", 409)
    checklist = version.checklist
    checklist.refresh_from_db()
    if not checklist.is_complete:
        raise ReleaseError("Finish tests, notes, and tag before publishing.")
    version.released_on = timezone.localdate()
    version.save(update_fields=["released_on"])
    return version


def build_changelog(product: Product) -> str:
    entries = list(product.entries.select_related("version").order_by("created_at", "id"))
    unreleased: list[Note] = []
    by_version: dict[int, list[Note]] = {}
    for entry in entries:
        note = Note(entry.kind, entry.text)
        if entry.version_id is None:
            unreleased.append(note)
        else:
            by_version.setdefault(entry.version_id, []).append(note)
    blocks = [
        VersionBlock(
            version.label,
            version.released_on,
            tuple(by_version.get(version.id, ())),
        )
        for version in product.versions.all()
    ]
    return render_changelog(product.name, blocks, unreleased, product.repository_url)
