from django.test import SimpleTestCase

from releases.lint import lint_notes


class LintTests(SimpleTestCase):
    def test_a_complete_note_is_clean(self):
        self.assertEqual(lint_notes([{"kind": "fixed", "text": "Correct the draft tag"}]), [])

    def test_missing_kind_and_empty_summary(self):
        issues = lint_notes(
            [
                {"id": 4, "kind": "", "text": "   "},
                {"kind": "security", "summary": ""},
                {"kind": "added", "text": "Queue the harbor lights"},
                {"id": 9, "text": "Kind was left off"},
            ]
        )
        self.assertEqual(
            [(issue.code, issue.index, issue.entry_id) for issue in issues],
            [
                ("missing_kind", 0, 4),
                ("empty_summary", 0, 4),
                ("missing_kind", 1, None),
                ("empty_summary", 1, None),
                ("missing_kind", 3, 9),
            ],
        )
        self.assertTrue(all(issue.message for issue in issues))

    def test_whitespace_kind_is_missing(self):
        issues = lint_notes([{"kind": "  ", "text": "Still a note"}])
        self.assertEqual([issue.code for issue in issues], ["missing_kind"])

    def test_empty_batch_is_clean(self):
        self.assertEqual(lint_notes([]), [])
