"""Semantic version parsing, precedence, and bumps.

Precedence follows Semantic Versioning 2.0.0 for the core numbers and
dot-separated pre-release identifiers. Build metadata is rejected.
"""

from __future__ import annotations

import re
from functools import total_ordering

_VERSION = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


CHANNELS = ("alpha", "beta", "rc")


class InvalidVersion(ValueError):
    """A version string or bump request broke semantic versioning rules."""


def _valid_ident(ident: str) -> bool:
    if not re.fullmatch(r"[0-9A-Za-z-]+", ident):
        return False
    if ident.isdigit() and ident != "0" and ident.startswith("0"):
        return False
    return True


def _ident_key(ident: str) -> tuple[int, int | str]:
    if ident.isdigit():
        return (0, int(ident))
    return (1, ident)


@total_ordering
class SemVer:
    def __init__(self, major: int, minor: int, patch: int, prerelease: str = "") -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        if min(major, minor, patch) < 0:
            raise InvalidVersion("Version numbers cannot be negative.")
        if prerelease:
            parts = prerelease.split(".")
            if any(not _valid_ident(part) for part in parts):
                raise InvalidVersion(
                    "Pre-release identifiers must be dot-separated alphanumerics without leading zeros."
                )

    def _key(self) -> tuple:
        # A final release outranks every pre-release of the same core version.
        if self.prerelease:
            pre: tuple = (0, tuple(_ident_key(part) for part in self.prerelease.split(".")))
        else:
            pre = (1, ())
        return (self.major, self.minor, self.patch, pre)

    @property
    def label(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{core}-{self.prerelease}"
        return core

    def bump(self, level: str) -> SemVer:
        if level == "major":
            return SemVer(self.major + 1, 0, 0)
        if level == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if level == "patch":
            if self.prerelease:
                return SemVer(self.major, self.minor, self.patch)
            return SemVer(self.major, self.minor, self.patch + 1)
        raise InvalidVersion("Bump level must be major, minor, or patch.")

    def advance_channel(self, channel: str) -> SemVer:
        """Step through alpha, then beta, then rc.

        A stable version opens the channel on the next patch (`1.2.3` becomes
        `1.2.4-alpha.1`). The same channel increments its number. A later
        channel replaces the label on the same core. An earlier channel is rejected.
        """
        if channel not in CHANNELS:
            raise InvalidVersion("Pre-release channel must be alpha, beta, or rc.")
        if not self.prerelease:
            return SemVer(self.major, self.minor, self.patch + 1, f"{channel}.1")

        parts = self.prerelease.split(".")
        head = parts[0]
        rank = {name: index for index, name in enumerate(CHANNELS)}
        if head not in rank:
            raise InvalidVersion(
                f"{self.label} uses a custom pre-release. Cut it with an explicit label instead of a channel bump."
            )
        if rank[channel] < rank[head]:
            raise InvalidVersion(
                f"Cannot move {self.label} back to {channel}. Channels advance from alpha to beta to rc."
            )
        if head == channel and len(parts) == 2 and parts[1].isdigit():
            return SemVer(self.major, self.minor, self.patch, f"{channel}.{int(parts[1]) + 1}")
        if head == channel and len(parts) == 1:
            return SemVer(self.major, self.minor, self.patch, f"{channel}.1")
        if head == channel:
            raise InvalidVersion(
                f"{self.label} is not a numbered {channel} tag. Use an explicit pre-release label to continue it."
            )
        return SemVer(self.major, self.minor, self.patch, f"{channel}.1")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._key() == other._key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._key() < other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return f"SemVer({self.label})"


def parse(text: str) -> SemVer:
    match = _VERSION.fullmatch(text.strip())
    if not match:
        raise InvalidVersion(f"{text!r} is not a semantic version.")
    major, minor, patch, prerelease = match.groups()
    return SemVer(int(major), int(minor), int(patch), prerelease or "")
