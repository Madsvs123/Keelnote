from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class ReleaseApiTests(TestCase):
    def setUp(self):
        self.keeper = User.objects.create_user("keeper", password="Sable-Harbor-42")
        self.other = User.objects.create_user("spectator", password="Sable-Harbor-42")
        self.client = APIClient()
        self.client.force_authenticate(self.keeper)

    def make_product(self, **overrides):
        payload = {"name": "Harbor", "summary": "A small release log", "repository_url": ""}
        payload.update(overrides)
        response = self.client.post("/api/products/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def add_note(self, product_id, text="Queue the harbor lights", kind="added", version=None):
        payload = {"product": product_id, "kind": kind, "text": text, "version": version}
        response = self.client.post("/api/entries/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def test_health_register_and_token(self):
        open_client = APIClient()
        health = open_client.get("/api/health/")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"name": "Keelnote", "ok": True})

        blocked = open_client.get("/api/products/")
        self.assertEqual(blocked.status_code, 401)

        short = open_client.post(
            "/api/auth/register/",
            {"username": "newkeeper", "password": "short"},
            format="json",
        )
        self.assertEqual(short.status_code, 400)

        registered = open_client.post(
            "/api/auth/register/",
            {"username": "newkeeper", "password": "Sable-Harbor-42"},
            format="json",
        )
        self.assertEqual(registered.status_code, 201)
        self.assertIn("access", registered.json())

        token = open_client.post(
            "/api/auth/token/",
            {"username": "keeper", "password": "Sable-Harbor-42"},
            format="json",
        )
        self.assertEqual(token.status_code, 200)
        open_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.json()['access']}")
        me = open_client.get("/api/auth/me/")
        self.assertEqual(me.json()["username"], "keeper")

    def test_product_slug_and_preview_from_zero(self):
        first = self.make_product()
        second = self.make_product()
        self.assertEqual(first["slug"], "harbor")
        self.assertEqual(second["slug"], "harbor-2")
        self.assertIsNone(first["latest"])
        self.assertEqual(
            first["next_versions"],
            {"major": "1.0.0", "minor": "0.1.0", "patch": "0.0.1"},
        )
        renamed = self.client.patch(f"/api/products/{first['id']}/", {"name": "Keel"}, format="json")
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["slug"], "keel")

        rejected = self.client.post(
            "/api/products/",
            {"name": "Remote", "repository_url": "ftp://example.com/harbor"},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        local = self.make_product(name="Local", repository_url="http://localhost:3000/harbor")
        self.assertEqual(local["repository_url"], "http://localhost:3000/harbor")

    def test_bump_moves_unreleased_notes_and_publish_waits_for_checklist(self):
        product = self.make_product(repository_url="https://github.com/acme/harbor")
        self.add_note(product["id"], "Queue the harbor lights", "added")
        self.add_note(product["id"], "Repair the tag writer", "fixed")

        bumped = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "minor"}, format="json")
        self.assertEqual(bumped.status_code, 201, bumped.content)
        version = bumped.json()
        self.assertEqual(version["label"], "0.1.0")
        self.assertIsNone(version["released_on"])
        self.assertEqual(version["note_count"], 2)
        self.assertEqual(
            version["checklist"],
            {
                "tests": False,
                "notes": False,
                "tag": False,
                "complete": False,
                "updated_at": version["checklist"]["updated_at"],
            },
        )

        waiting = self.client.get("/api/entries/", {"product": product["id"], "bucket": "unreleased"})
        self.assertEqual(waiting.json(), [])
        moved = self.client.get("/api/entries/", {"product": product["id"], "version": version["id"]})
        self.assertEqual({item["text"] for item in moved.json()}, {"Queue the harbor lights", "Repair the tag writer"})

        early = self.client.post(f"/api/versions/{version['id']}/publish/")
        self.assertEqual(early.status_code, 400)

        for field in ("tests", "notes", "tag"):
            checked = self.client.patch(
                f"/api/versions/{version['id']}/checklist/",
                {field: True},
                format="json",
            )
            self.assertEqual(checked.status_code, 200, checked.content)

        published = self.client.post(f"/api/versions/{version['id']}/publish/")
        self.assertEqual(published.status_code, 200, published.content)
        self.assertEqual(published.json()["released_on"], timezone.localdate().isoformat())
        self.assertTrue(published.json()["checklist"]["complete"])

        locked = self.client.patch(
            f"/api/versions/{version['id']}/checklist/",
            {"tests": False},
            format="json",
        )
        self.assertEqual(locked.status_code, 409)
        kept = self.client.delete(f"/api/versions/{version['id']}/")
        self.assertEqual(kept.status_code, 409)

        refreshed = self.client.get(f"/api/products/{product['id']}/")
        self.assertEqual(refreshed.json()["latest"], "0.1.0")
        self.assertEqual(refreshed.json()["unreleased_count"], 0)
        self.assertEqual(refreshed.json()["next_versions"]["patch"], "0.1.1")

        changelog = self.client.get(f"/api/products/{product['id']}/changelog/").json()["markdown"]
        marker = f"## [0.1.0] - {published.json()['released_on']}"
        head, _, body = changelog.partition(marker)
        self.assertIn("## [Unreleased]", head)
        self.assertNotIn("Queue the harbor lights", head)
        self.assertIn("### Added", body)
        self.assertIn("- Queue the harbor lights", body)
        self.assertIn("### Fixed", body)
        self.assertIn("[Unreleased]: https://github.com/acme/harbor/compare/v0.1.0...HEAD", changelog)

    def test_prerelease_patch_promotes_and_duplicate_is_rejected(self):
        product = self.make_product(name="Beacon")
        self.add_note(product["id"], "Sketch the rc", "changed")
        candidate = self.client.post(
            f"/api/products/{product['id']}/bump/",
            {"level": "minor", "prerelease": "rc.1"},
            format="json",
        )
        self.assertEqual(candidate.status_code, 201, candidate.content)
        self.assertEqual(candidate.json()["label"], "0.1.0-rc.1")
        self.assertEqual(candidate.json()["note_count"], 1)

        preview = self.client.get(f"/api/products/{product['id']}/").json()
        self.assertEqual(preview["latest"], "0.1.0-rc.1")
        self.assertEqual(
            preview["next_versions"],
            {"major": "1.0.0", "minor": "0.2.0", "patch": "0.1.0"},
        )

        duplicate = self.client.post(
            f"/api/products/{product['id']}/bump/",
            {"level": "patch", "prerelease": "rc.1"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 409)

        self.add_note(product["id"], "Promote the rc", "fixed")
        stable = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "patch"}, format="json")
        self.assertEqual(stable.status_code, 201, stable.content)
        self.assertEqual(stable.json()["label"], "0.1.0")
        self.assertEqual(stable.json()["note_count"], 1)

        listed = self.client.get("/api/versions/", {"product": product["id"]}).json()
        self.assertEqual([item["label"] for item in listed], ["0.1.0", "0.1.0-rc.1"])

    def test_deleting_a_draft_returns_notes_to_the_bucket(self):
        product = self.make_product(name="Ledge")
        note = self.add_note(product["id"], "Hold this note")
        version = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "patch"}, format="json").json()
        self.assertEqual(version["label"], "0.0.1")
        removed = self.client.delete(f"/api/versions/{version['id']}/")
        self.assertEqual(removed.status_code, 204)
        waiting = self.client.get("/api/entries/", {"product": product["id"], "bucket": "unreleased"}).json()
        self.assertEqual(waiting[0]["id"], note["id"])
        self.assertIsNone(waiting[0]["version"])
        self.assertEqual(self.client.get("/api/versions/", {"product": product["id"]}).json(), [])

    def test_channel_bumps_advance_alpha_then_beta_then_rc(self):
        product = self.make_product(name="Channel")
        self.add_note(product["id"], "Open the alpha")
        alpha = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "alpha"}, format="json")
        self.assertEqual(alpha.status_code, 201, alpha.content)
        self.assertEqual(alpha.json()["label"], "0.0.1-alpha.1")
        self.assertEqual(alpha.json()["prerelease"], "alpha.1")

        preview = self.client.get(f"/api/products/{product['id']}/").json()
        self.assertEqual(
            preview["next_channels"],
            {"alpha": "0.0.1-alpha.2", "beta": "0.0.1-beta.1", "rc": "0.0.1-rc.1"},
        )

        self.add_note(product["id"], "Continue the alpha", "changed")
        again = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "alpha"}, format="json")
        self.assertEqual(again.status_code, 201, again.content)
        self.assertEqual(again.json()["label"], "0.0.1-alpha.2")

        self.add_note(product["id"], "Move to beta", "fixed")
        beta = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "beta"}, format="json")
        self.assertEqual(beta.status_code, 201, beta.content)
        self.assertEqual(beta.json()["label"], "0.0.1-beta.1")

        mixed = self.client.post(
            f"/api/products/{product['id']}/bump/",
            {"level": "rc", "prerelease": "rc.9"},
            format="json",
        )
        self.assertEqual(mixed.status_code, 400)

        backwards = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "alpha"}, format="json")
        self.assertEqual(backwards.status_code, 400)

        self.add_note(product["id"], "Candidate", "changed")
        rc = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "rc"}, format="json")
        self.assertEqual(rc.status_code, 201, rc.content)
        self.assertEqual(rc.json()["label"], "0.0.1-rc.1")
        self.assertEqual(rc.json()["note_count"], 1)

    def publish(self, version_id):
        for field in ("tests", "notes", "tag"):
            checked = self.client.patch(
                f"/api/versions/{version_id}/checklist/",
                {field: True},
                format="json",
            )
            self.assertEqual(checked.status_code, 200, checked.content)
        published = self.client.post(f"/api/versions/{version_id}/publish/")
        self.assertEqual(published.status_code, 200, published.content)
        return published.json()

    def test_yank_keeps_the_notes_on_the_published_version(self):
        product = self.make_product(name="Mooring")
        note = self.add_note(product["id"], "Tighten the stern line", "fixed")
        version = self.client.post(f"/api/products/{product['id']}/bump/", {"level": "patch"}, format="json").json()
        draft = self.client.post(
            f"/api/versions/{version['id']}/yank/",
            {"reason": "Too early"},
            format="json",
        )
        self.assertEqual(draft.status_code, 400)

        self.publish(version["id"])
        missing = self.client.post(f"/api/versions/{version['id']}/yank/", {"reason": "  "}, format="json")
        self.assertEqual(missing.status_code, 400)

        yanked = self.client.post(
            f"/api/versions/{version['id']}/yank/",
            {"reason": "The tag points at the wrong commit"},
            format="json",
        )
        self.assertEqual(yanked.status_code, 200, yanked.content)
        body = yanked.json()
        self.assertEqual(body["yank_reason"], "The tag points at the wrong commit")
        self.assertEqual(body["yanked_on"], timezone.localdate().isoformat())
        self.assertEqual(body["note_count"], 1)
        self.assertIsNotNone(body["released_on"])

        kept = self.client.get("/api/entries/", {"product": product["id"], "version": version["id"]}).json()
        self.assertEqual(kept[0]["id"], note["id"])
        self.assertEqual(kept[0]["text"], "Tighten the stern line")
        self.assertEqual(kept[0]["version"], version["id"])

        again = self.client.post(
            f"/api/versions/{version['id']}/yank/",
            {"reason": "Already withdrawn"},
            format="json",
        )
        self.assertEqual(again.status_code, 409)
        removed = self.client.delete(f"/api/versions/{version['id']}/")
        self.assertEqual(removed.status_code, 409)

        stranger = APIClient()
        stranger.force_authenticate(self.other)
        hidden = stranger.post(
            f"/api/versions/{version['id']}/yank/",
            {"reason": "Not your release"},
            format="json",
        )
        self.assertEqual(hidden.status_code, 404)

    def test_other_maintainer_cannot_see_the_log(self):
        product = self.make_product(name="Private")
        self.add_note(product["id"], "Mine alone")
        stranger = APIClient()
        stranger.force_authenticate(self.other)
        self.assertEqual(stranger.get("/api/products/").json(), [])
        self.assertEqual(stranger.get(f"/api/products/{product['id']}/").status_code, 404)
        leaked = stranger.post(
            "/api/entries/",
            {"product": product["id"], "kind": "added", "text": "Not yours"},
            format="json",
        )
        self.assertEqual(leaked.status_code, 400)
        self.assertEqual(stranger.get("/api/entries/").json(), [])
