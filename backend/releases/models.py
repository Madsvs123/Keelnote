from django.conf import settings
from django.db import models

from .semver import SemVer


class Product(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    summary = models.CharField(max_length=280, blank=True, default="")
    repository_url = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="unique_product_slug_per_owner"),
        ]

    def __str__(self) -> str:
        return self.name


class Version(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="versions")
    major = models.PositiveIntegerField()
    minor = models.PositiveIntegerField()
    patch = models.PositiveIntegerField()
    prerelease = models.CharField(max_length=64, blank=True, default="")
    released_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-major", "-minor", "-patch", "prerelease", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "major", "minor", "patch", "prerelease"],
                name="unique_version_identity",
            ),
        ]

    def as_semver(self) -> SemVer:
        return SemVer(self.major, self.minor, self.patch, self.prerelease)

    @property
    def label(self) -> str:
        return self.as_semver().label

    def __str__(self) -> str:
        return f"{self.product.name} {self.label}"


class ChangelogEntry(models.Model):
    class Kind(models.TextChoices):
        ADDED = "added", "Added"
        CHANGED = "changed", "Changed"
        FIXED = "fixed", "Fixed"
        REMOVED = "removed", "Removed"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="entries")
    version = models.ForeignKey(
        Version,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entries",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["product", "version"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}: {self.text[:48]}"


class ReleaseChecklist(models.Model):
    version = models.OneToOneField(Version, on_delete=models.CASCADE, related_name="checklist")
    tests = models.BooleanField(default=False)
    notes = models.BooleanField(default=False)
    tag = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_complete(self) -> bool:
        return self.tests and self.notes and self.tag

    def __str__(self) -> str:
        return f"Checklist for {self.version}"
