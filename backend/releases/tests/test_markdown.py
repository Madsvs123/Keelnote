from datetime import date

from django.test import SimpleTestCase

from releases.markdown import KIND_ORDER, Note, VersionBlock, render_changelog
from releases.models import ChangelogEntry


class MarkdownTests(SimpleTestCase):
    def test_kinds_match_the_entry_model(self):
        self.assertEqual(set(KIND_ORDER), set(ChangelogEntry.Kind.values))

    def test_empty_log_keeps_the_unreleased_bucket(self):
        text = render_changelog("Harbor", [], [])
        self.assertEqual(
            text,
            "\n".join(
                [
                    "# Changelog",
                    "",
                    "All notable changes to Harbor are recorded in this file.",
                    "",
                    "Version numbers follow semantic versioning. Each release groups work into added, changed, fixed, and removed.",
                    "",
                    "## [Unreleased]",
                    "",
                    "_Nothing is waiting in the unreleased bucket._",
                    "",
                ]
            ),
        )

    def test_groups_kinds_and_keeps_multiline_notes(self):
        text = render_changelog(
            "Harbor",
            [
                VersionBlock(
                    "1.2.0",
                    date(2026, 10, 1),
                    (
                        Note("fixed", "Correct the draft tag"),
                        Note("removed", "Drop the legacy export"),
                        Note("changed", "Rewrite the exporter\nKeep the old flag for one release"),
                    ),
                )
            ],
            [Note("added", "Queue the public feed")],
        )
        self.assertIn("## [Unreleased]\n\n### Added\n\n- Queue the public feed\n", text)
        version_at = text.index("## [1.2.0] - 2026-10-01")
        added_at = text.index("### Added")
        self.assertLess(added_at, version_at)
        body = text[version_at:]
        self.assertLess(body.index("### Changed"), body.index("### Fixed"))
        self.assertLess(body.index("### Fixed"), body.index("### Removed"))
        self.assertIn("- Rewrite the exporter\n  Keep the old flag for one release", body)

    def test_orders_versions_and_links_the_newest_published_tag(self):
        text = render_changelog(
            "Harbor",
            [
                VersionBlock("1.0.0", date(2026, 8, 1), (Note("added", "Start the log"),)),
                VersionBlock("1.3.0", None, ()),
                VersionBlock("1.2.0", date(2026, 10, 1), (Note("fixed", "Correct the draft tag"),)),
            ],
            [Note("added", "Queue the next note")],
            "https://github.com/acme/harbor/",
        )
        self.assertLess(text.index("## [1.3.0] - draft"), text.index("## [1.2.0] - 2026-10-01"))
        self.assertLess(text.index("## [1.2.0] - 2026-10-01"), text.index("## [1.0.0] - 2026-08-01"))
        self.assertIn("_No notes were recorded for this version._", text)
        self.assertIn(
            "[Unreleased]: https://github.com/acme/harbor/compare/v1.2.0...HEAD",
            text,
        )
        self.assertIn("[1.3.0]: https://github.com/acme/harbor/releases/tag/v1.3.0", text)
        self.assertNotIn("https://github.com/acme/harbor//", text)

    def test_yanked_version_keeps_its_notes_and_records_the_reason(self):
        text = render_changelog(
            "Harbor",
            [
                VersionBlock(
                    "1.2.0",
                    date(2026, 10, 1),
                    (Note("fixed", "Correct the draft tag"),),
                    date(2026, 10, 3),
                    "The tag points at the wrong commit",
                )
            ],
            [],
        )
        self.assertIn("## [1.2.0] - 2026-10-01 [YANKED]", text)
        self.assertIn("Yanked on 2026-10-03: The tag points at the wrong commit", text)
        self.assertIn("- Correct the draft tag", text)
        self.assertLess(text.index("[YANKED]"), text.index("Correct the draft tag"))

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            render_changelog("Harbor", [], [Note("security", "Tighten a header")])
