from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from releases.models import ChangelogEntry, Product, Version
from releases.semver import InvalidVersion, parse


class Command(BaseCommand):
    help = "Add a changelog note to one of your products."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--product", required=True, help="Product slug.")
        parser.add_argument("--kind", required=True)
        parser.add_argument("--text", required=True)
        parser.add_argument(
            "--release",
            default="",
            help="Version label such as 1.2.0 or 1.2.0-rc.1. Omit this to leave the note unreleased.",
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"No maintainer named {username}.") from exc
        slug = options["product"].strip()
        try:
            product = Product.objects.get(owner=user, slug=slug)
        except Product.DoesNotExist as exc:
            raise CommandError(f"No product with slug {slug}.") from exc

        kind = options["kind"].strip()
        if kind not in ChangelogEntry.Kind.values:
            raise CommandError("Kind must be added, changed, fixed, or removed.")
        text = options["text"].strip()
        if not text:
            raise CommandError("Write a note before saving.")
        if len(text) > 2000:
            raise CommandError("Keep the note under 2000 characters.")

        version = None
        label = options["release"].strip()
        if label:
            try:
                parsed = parse(label)
            except InvalidVersion as exc:
                raise CommandError(str(exc)) from exc
            try:
                version = product.versions.get(
                    major=parsed.major,
                    minor=parsed.minor,
                    patch=parsed.patch,
                    prerelease=parsed.prerelease,
                )
            except Version.DoesNotExist as exc:
                raise CommandError(f"{label} is not a version of {slug}.") from exc

        entry = ChangelogEntry.objects.create(
            product=product,
            version=version,
            kind=kind,
            text=text,
        )
        where = version.label if version else "unreleased"
        self.stdout.write(f"Added {entry.kind} note {entry.pk} to {slug} ({where}).")
