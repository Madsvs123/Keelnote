from urllib.parse import urlsplit

from rest_framework import serializers

from .models import ChangelogEntry, Product, ReleaseChecklist, Version
from .semver import InvalidVersion
from .services import version_base


class ChecklistSerializer(serializers.ModelSerializer):
    complete = serializers.BooleanField(source="is_complete", read_only=True)

    class Meta:
        model = ReleaseChecklist
        fields = ["tests", "notes", "tag", "complete", "updated_at"]
        read_only_fields = ["updated_at"]


class VersionSerializer(serializers.ModelSerializer):
    label = serializers.ReadOnlyField()
    checklist = ChecklistSerializer(read_only=True)
    note_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Version
        fields = [
            "id",
            "product",
            "label",
            "major",
            "minor",
            "patch",
            "prerelease",
            "released_on",
            "checklist",
            "note_count",
            "created_at",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "summary", "repository_url"]
        extra_kwargs = {
            "summary": {"allow_blank": True, "required": False},
            "repository_url": {"allow_blank": True, "required": False},
        }

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError("Use at least 2 characters.")
        return cleaned

    def validate_summary(self, value: str) -> str:
        return value.strip()

    def validate_repository_url(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ""
        parsed = urlsplit(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise serializers.ValidationError("Use an http or https URL.")
        return cleaned


class ProductSerializer(serializers.ModelSerializer):
    latest = serializers.SerializerMethodField()
    next_versions = serializers.SerializerMethodField()
    next_channels = serializers.SerializerMethodField()
    unreleased_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "summary",
            "repository_url",
            "latest",
            "next_versions",
            "next_channels",
            "unreleased_count",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bases: dict[int, tuple] = {}

    def _base(self, obj: Product):
        if obj.pk not in self._bases:
            self._bases[obj.pk] = version_base(obj)
        return self._bases[obj.pk]

    def get_latest(self, obj: Product):
        current, _base = self._base(obj)
        return current.label if current else None

    def get_next_versions(self, obj: Product):
        _current, base = self._base(obj)
        return {level: base.bump(level).label for level in ("major", "minor", "patch")}

    def get_next_channels(self, obj: Product):
        _current, base = self._base(obj)
        labels: dict[str, str | None] = {}
        for channel in ("alpha", "beta", "rc"):
            try:
                labels[channel] = base.advance_channel(channel).label
            except InvalidVersion:
                labels[channel] = None
        return labels


class EntrySerializer(serializers.ModelSerializer):
    version_label = serializers.SerializerMethodField()

    class Meta:
        model = ChangelogEntry
        fields = ["id", "product", "version", "version_label", "kind", "text", "created_at"]

    def get_version_label(self, obj: ChangelogEntry):
        if obj.version_id is None:
            return None
        return obj.version.label


class EntryWriteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        error_messages={"blank": "Write a note before saving."},
    )
    version = serializers.PrimaryKeyRelatedField(
        queryset=Version.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = ChangelogEntry
        fields = ["product", "version", "kind", "text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["product"].queryset = Product.objects.filter(owner=request.user)
            self.fields["version"].queryset = Version.objects.filter(product__owner=request.user)
        if self.instance is not None:
            self.fields["product"].read_only = True

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        if "version" in attrs:
            version = attrs["version"]
        elif self.instance is not None:
            version = self.instance.version
        else:
            version = None
        if version is not None and product is not None and version.product_id != product.id:
            raise serializers.ValidationError({"version": "That version belongs to another product."})
        return attrs
