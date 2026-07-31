import shutil
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.staging import stage_persona_inbox


class PersonaInboxStagingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-staging-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True)
        (self.repo_root / "wiki" / "products").mkdir(parents=True)
        (self.repo_root / "wiki" / "review" / "demo").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").write_text(
            "Evidence bundle",
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "products" / "demo.json").write_text(
            '{"slug":"demo"}',
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "review" / "demo" / "vendor.json").write_text(
            '{"side":"vendor"}',
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "review" / "demo" / "skeptic.json").write_text(
            '{"side":"skeptic"}',
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "review" / "demo" / "notes.txt").write_text(
            "not allowlisted",
            encoding="utf-8",
        )

    def test_vendor_and_skeptic_inboxes_include_only_evidence_and_draft_profile(self):
        # Break caught: vendor/skeptic staging leaks peer review output or copies arbitrary review files.
        vendor_inbox = stage_persona_inbox(self.repo_root, "demo", "vendor")
        skeptic_inbox = stage_persona_inbox(self.repo_root, "demo", "skeptic")

        self.assertEqual(
            ["demo.json", "evidence.md"],
            sorted(path.name for path in vendor_inbox.iterdir()),
        )
        self.assertEqual(
            ["demo.json", "evidence.md"],
            sorted(path.name for path in skeptic_inbox.iterdir()),
        )
        self.assertFalse((vendor_inbox / "skeptic.json").exists())
        self.assertFalse((skeptic_inbox / "vendor.json").exists())

    def test_arbiter_inbox_receives_only_evidence_and_both_review_outputs(self):
        # Break caught: arbiter misses one review or receives the draft profile / stray files.
        inbox = stage_persona_inbox(self.repo_root, "demo", "arbiter")

        self.assertEqual(
            ["evidence.md", "skeptic.json", "vendor.json"],
            sorted(path.name for path in inbox.iterdir()),
        )
        self.assertFalse((inbox / "demo.json").exists())
        self.assertFalse((inbox / "notes.txt").exists())

    def test_stage_persona_inbox_rejects_slug_path_escape(self):
        # Break caught: a crafted slug can escape wiki/ and stage arbitrary repository files.
        with self.assertRaisesRegex(ValueError, "slug escapes repository root"):
            stage_persona_inbox(self.repo_root, "../escape", "vendor")

    def test_stage_persona_inbox_rejects_symlinked_sources(self):
        # Break caught: staged inputs follow symlinks and expose bytes outside the allowlisted tree.
        secret = self.tempdir / "secret.txt"
        secret.write_text("outside bytes", encoding="utf-8")
        evidence_path = self.repo_root / "wiki" / "raw" / "demo" / "evidence.md"
        evidence_path.unlink()
        evidence_path.symlink_to(secret)

        with self.assertRaisesRegex(ValueError, "refuses symlinked source"):
            stage_persona_inbox(self.repo_root, "demo", "vendor")


if __name__ == "__main__":
    unittest.main()
