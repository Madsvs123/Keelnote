from django.contrib import admin

from .models import ChangelogEntry, NoteTemplate, Product, ReleaseChecklist, Version


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "slug", "updated_at")
    search_fields = ("name", "slug", "owner__username")


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("product", "major", "minor", "patch", "prerelease", "released_on", "yanked_on")
    list_filter = ("released_on", "yanked_on")


@admin.register(ChangelogEntry)
class ChangelogEntryAdmin(admin.ModelAdmin):
    list_display = ("product", "kind", "version", "created_at")
    list_filter = ("kind",)


@admin.register(NoteTemplate)
class NoteTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "kind", "created_at")
    list_filter = ("kind",)


@admin.register(ReleaseChecklist)
class ReleaseChecklistAdmin(admin.ModelAdmin):
    list_display = ("version", "tests", "notes", "tag")
