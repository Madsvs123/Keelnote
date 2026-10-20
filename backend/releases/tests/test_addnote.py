from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from releases.models import ChangelogEntry, Product, Version


class AddNoteCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("keeper", password="Sable-Harbor-42")
        self.product = Product.objects.create(owner=self.user, name="Harbor", slug="harbor")
        self.version = Version.objects.create(product=self.product, major=0, minor=1, patch=0)

    def test_adds_an_unreleased_note(self):
        output = StringIO()
        call_command(
            "addnote",
            "--username",
            "keeper",
            "--product",
            "harbor",
            "--kind",
            "fixed",
            "--text",
            "Repair the tag writer",
            stdout=output,
        )
        entry = ChangelogEntry.objects.get()
        self.assertIsNone(entry.version_id)
        self.assertEqual(entry.kind, "fixed")
        self.assertEqual(entry.text, "Repair the tag writer")
        self.assertIn(f"Added fixed note {entry.pk} to harbor (unreleased).", output.getvalue())

    def test_attaches_a_note_to_an_existing_version(self):
        call_command(
            "addnote",
            "--username",
            "keeper",
            "--product",
            "harbor",
            "--kind",
            "added",
            "--text",
            "Queue the harbor lights",
            "--release",
            "0.1.0",
        )
        entry = ChangelogEntry.objects.get()
        self.assertEqual(entry.version_id, self.version.id)

    def test_rejects_a_blank_summary_unknown_kind_and_missing_version(self):
        with self.assertRaises(CommandError):
            call_command(
                "addnote",
                "--username",
                "keeper",
                "--product",
                "harbor",
                "--kind",
                "fixed",
                "--text",
                "   ",
            )
        with self.assertRaises(CommandError):
            call_command(
                "addnote",
                "--username",
                "keeper",
                "--product",
                "harbor",
                "--kind",
                "security",
                "--text",
                "Tighten a header",
            )
        with self.assertRaises(CommandError):
            call_command(
                "addnote",
                "--username",
                "keeper",
                "--product",
                "harbor",
                "--kind",
                "fixed",
                "--text",
                "Missing version",
                "--release",
                "9.9.9",
            )
        self.assertEqual(ChangelogEntry.objects.count(), 0)
