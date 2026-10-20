from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChangelogEntry, Product, Version
from .permissions import OwnsProduct
from .serializers import (
    ChecklistSerializer,
    EntrySerializer,
    EntryWriteSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    VersionSerializer,
)
from .services import ReleaseError, build_changelog, cut_release, publish_version, unique_slug, yank_version


def visible_versions(user):
    return (
        Version.objects.filter(product__owner=user)
        .select_related("checklist", "product")
        .annotate(note_count=Count("entries"))
    )


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, OwnsProduct]

    def get_queryset(self):
        return (
            Product.objects.filter(owner=self.request.user)
            .prefetch_related("versions")
            .annotate(unreleased_count=Count("entries", filter=Q(entries__version__isnull=True)))
            .order_by("name", "id")
        )

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ProductWriteSerializer
        return ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                product = serializer.save(
                    owner=request.user,
                    slug=unique_slug(request.user, serializer.validated_data["name"]),
                )
        except IntegrityError:
            return Response({"detail": "Choose a different product name."}, status=status.HTTP_409_CONFLICT)
        product = self.get_queryset().get(pk=product.pk)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        name = serializer.validated_data.get("name", serializer.instance.name)
        slug = serializer.instance.slug
        if name != serializer.instance.name:
            slug = unique_slug(serializer.instance.owner, name, exclude_pk=serializer.instance.pk)
        serializer.save(slug=slug)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        product = self.get_queryset().get(pk=instance.pk)
        return Response(ProductSerializer(product).data)

    @action(detail=True, methods=["get"])
    def changelog(self, request, pk=None):
        product = self.get_object()
        return Response({"markdown": build_changelog(product)})

    @action(detail=True, methods=["post"])
    def bump(self, request, pk=None):
        product = self.get_object()
        level = request.data.get("level", "")
        prerelease = request.data.get("prerelease", "")
        if not isinstance(level, str) or not isinstance(prerelease, str):
            return Response(
                {"detail": "Level and pre-release must be text."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            version = cut_release(product, level, prerelease)
        except ReleaseError as exc:
            return Response({"detail": str(exc)}, status=exc.status)
        version = visible_versions(request.user).get(pk=version.pk)
        return Response(VersionSerializer(version).data, status=status.HTTP_201_CREATED)


class VersionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated, OwnsProduct]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = visible_versions(self.request.user)
        if self.action == "list":
            product_id = self.request.query_params.get("product")
            if product_id:
                queryset = queryset.filter(product_id=product_id)
        return queryset

    def list(self, request, *args, **kwargs):
        versions = list(self.filter_queryset(self.get_queryset()))
        versions.sort(key=lambda version: version.as_semver(), reverse=True)
        return Response(self.get_serializer(versions, many=True).data)

    def destroy(self, request, *args, **kwargs):
        version = self.get_object()
        if version.released_on is not None:
            return Response(
                {"detail": "Published versions stay in the record."},
                status=status.HTTP_409_CONFLICT,
            )
        version.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"])
    def checklist(self, request, pk=None):
        version = self.get_object()
        if version.released_on is not None:
            return Response(
                {"detail": "Published checklists are locked."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ChecklistSerializer(version.checklist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        version = visible_versions(request.user).get(pk=version.pk)
        return Response(self.get_serializer(version).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        version = self.get_object()
        try:
            publish_version(version)
        except ReleaseError as exc:
            return Response({"detail": str(exc)}, status=exc.status)
        version = visible_versions(request.user).get(pk=version.pk)
        return Response(self.get_serializer(version).data)

    @action(detail=True, methods=["post"])
    def yank(self, request, pk=None):
        version = self.get_object()
        reason = request.data.get("reason", "")
        if not isinstance(reason, str):
            return Response({"detail": "The yank reason must be text."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            yank_version(version, reason)
        except ReleaseError as exc:
            return Response({"detail": str(exc)}, status=exc.status)
        version = visible_versions(request.user).get(pk=version.pk)
        return Response(self.get_serializer(version).data)


class EntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, OwnsProduct]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = ChangelogEntry.objects.filter(product__owner=self.request.user).select_related(
            "version", "product"
        )
        if self.action != "list":
            return queryset
        product_id = self.request.query_params.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        bucket = self.request.query_params.get("bucket")
        version_id = self.request.query_params.get("version")
        if bucket == "unreleased":
            queryset = queryset.filter(version__isnull=True)
        elif version_id:
            queryset = queryset.filter(version_id=version_id)
        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return EntryWriteSerializer
        return EntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        entry = self.get_queryset().get(pk=serializer.instance.pk)
        return Response(EntrySerializer(entry).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        entry = self.get_object()
        serializer = self.get_serializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        entry = self.get_queryset().get(pk=entry.pk)
        return Response(EntrySerializer(entry).data)
