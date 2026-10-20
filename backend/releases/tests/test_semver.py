from django.test import SimpleTestCase

from releases.semver import CHANNELS, InvalidVersion, SemVer, parse


class SemVerTests(SimpleTestCase):
    def test_precedence_follows_the_spec_chain(self):
        labels = [
            "1.0.0-rc.1",
            "1.0.0-alpha",
            "1.0.0",
            "1.0.0-beta.11",
            "1.0.0-alpha.beta",
            "1.0.0-beta.2",
            "1.0.0-beta",
            "1.0.0-alpha.1",
        ]
        ordered = [version.label for version in sorted(parse(label) for label in labels)]
        self.assertEqual(
            ordered,
            [
                "1.0.0-alpha",
                "1.0.0-alpha.1",
                "1.0.0-alpha.beta",
                "1.0.0-beta",
                "1.0.0-beta.2",
                "1.0.0-beta.11",
                "1.0.0-rc.1",
                "1.0.0",
            ],
        )

    def test_numeric_core_ordering(self):
        self.assertLess(parse("1.9.9"), parse("2.0.0"))
        self.assertLess(parse("1.2.2"), parse("1.2.3"))
        self.assertEqual(parse("1.2.3"), SemVer(1, 2, 3))
        self.assertNotEqual(parse("1.0.0"), parse("1.0.1"))

    def test_longer_prerelease_has_higher_precedence(self):
        self.assertLess(parse("1.0.0-alpha.1"), parse("1.0.0-alpha.1.1"))

    def test_numeric_identifiers_rank_below_words(self):
        self.assertLess(parse("1.0.0-1"), parse("1.0.0-alpha"))
        self.assertEqual(parse("1.0.0-0").prerelease, "0")

    def test_rejects_non_semver(self):
        for text in ["", "1.2", "v1.2.3", "01.2.3", "1.02.3", "1.2.03", "1.2.3+build", "1.2.3-01", "1.2.3-rc..1"]:
            with self.assertRaises(InvalidVersion):
                parse(text)

    def test_bumps(self):
        current = parse("1.2.3")
        self.assertEqual(current.bump("patch").label, "1.2.4")
        self.assertEqual(current.bump("minor").label, "1.3.0")
        self.assertEqual(current.bump("major").label, "2.0.0")

    def test_patch_from_prerelease_promotes_same_core(self):
        candidate = parse("1.2.3-rc.1")
        self.assertEqual(candidate.bump("patch").label, "1.2.3")
        self.assertEqual(candidate.bump("minor").label, "1.3.0")
        self.assertEqual(candidate.bump("major").label, "2.0.0")

    def test_first_bumps_from_zero(self):
        origin = SemVer(0, 0, 0)
        self.assertEqual(origin.bump("patch").label, "0.0.1")
        self.assertEqual(origin.bump("minor").label, "0.1.0")
        self.assertEqual(origin.bump("major").label, "1.0.0")

    def test_unknown_level(self):
        with self.assertRaises(InvalidVersion):
            parse("1.0.0").bump("build")

    def test_label_round_trip(self):
        version = parse("2.4.6-rc.2")
        self.assertEqual(parse(version.label), version)

    def test_channel_order_is_alpha_beta_rc(self):
        self.assertEqual(CHANNELS, ("alpha", "beta", "rc"))

    def test_stable_version_opens_a_numbered_channel_on_the_next_patch(self):
        current = parse("1.2.3")
        self.assertEqual(current.advance_channel("alpha").label, "1.2.4-alpha.1")
        self.assertEqual(current.advance_channel("beta").label, "1.2.4-beta.1")
        self.assertEqual(current.advance_channel("rc").label, "1.2.4-rc.1")
        self.assertEqual(SemVer(0, 0, 0).advance_channel("alpha").label, "0.0.1-alpha.1")

    def test_same_channel_increments_and_later_channels_keep_the_core(self):
        alpha = parse("1.2.4-alpha.1")
        self.assertEqual(alpha.advance_channel("alpha").label, "1.2.4-alpha.2")
        self.assertEqual(alpha.advance_channel("beta").label, "1.2.4-beta.1")
        beta = parse("1.2.4-beta")
        self.assertEqual(beta.advance_channel("beta").label, "1.2.4-beta.1")
        self.assertEqual(parse("1.2.4-beta.1").advance_channel("rc").label, "1.2.4-rc.1")
        self.assertEqual(parse("1.2.4-rc.1").advance_channel("rc").label, "1.2.4-rc.2")

    def test_channel_cannot_move_backwards_or_continue_a_custom_label(self):
        with self.assertRaises(InvalidVersion):
            parse("1.2.4-rc.1").advance_channel("alpha")
        with self.assertRaises(InvalidVersion):
            parse("1.2.4-rc.1").advance_channel("beta")
        with self.assertRaises(InvalidVersion):
            parse("1.2.4-preview.1").advance_channel("alpha")
        with self.assertRaises(InvalidVersion):
            parse("1.2.4-alpha.beta").advance_channel("alpha")
        with self.assertRaises(InvalidVersion):
            parse("1.2.3").advance_channel("nightly")
