import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.compiler import compile_readme, replace_compiled_block
from tools.aris_geo.publication import build_publication


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "profound"


class PublicationDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-publication-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)

    def test_catalog_reproduces_committed_profiles_evidence_and_readme(self):
        catalog = json.loads((REPO_ROOT / "wiki" / "catalog.json").read_text(encoding="utf-8"))
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        (self.repo_root / "README.md").write_text(
            replace_compiled_block(readme, ""),
            encoding="utf-8",
        )

        profiles = build_publication(self.repo_root, catalog)
        _, compiled = compile_readme(self.repo_root)
        (self.repo_root / "README.md").write_text(compiled, encoding="utf-8")

        self.assertEqual(14, len(profiles))
        self._assert_matching_tree(REPO_ROOT / "wiki" / "products", self.repo_root / "wiki" / "products")
        self._assert_matching_tree(REPO_ROOT / "wiki" / "raw", self.repo_root / "wiki" / "raw")
        for name in ("queue.json", "sources.json"):
            self.assertEqual(
                (REPO_ROOT / "wiki" / name).read_text(encoding="utf-8"),
                (self.repo_root / "wiki" / name).read_text(encoding="utf-8"),
            )
        self.assertEqual(readme, compiled)

    def test_synthetic_fixture_is_test_only_and_excluded_from_publication(self):
        fixture_profile = json.loads(
            (FIXTURE_ROOT / "wiki" / "products" / "profound.json").read_text(encoding="utf-8")
        )
        published_profile = json.loads(
            (REPO_ROOT / "wiki" / "products" / "profound.json").read_text(encoding="utf-8")
        )

        self.assertIn("Synthetic Offline Fixture", fixture_profile["name_en"]["v"])
        self.assertEqual("Profound", published_profile["name_en"]["v"])
        self.assertNotIn("example.invalid", published_profile["homepage"]["v"])
        self.assertNotEqual(fixture_profile, published_profile)

    def test_repository_docs_describe_real_report_reproduction_and_limits(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        methodology = (REPO_ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8")

        for snippet in (
            "收录 14 个真实对象",
            "Python 3.11+",
            "ARIS-Code v0.4.21+",
            "python3 tools/build_publication.py",
            "python3 -m unittest discover -s tests -v",
            "python3 tools/verify_evidence.py --strict",
            "python3 tools/score.py --check",
            "python3 tools/compile_readme.py --check",
            "python3 tools/geo_loop.py",
            "--live",
            "Model phases send the staged evidence",
            "Do not commit API keys",
        ):
            self.assertIn(snippet, readme)

        for snippet in (
            "14 deliberately heterogeneous objects",
            "synthetic Profound fixture",
            "「未披露」不等于「没有」",
            "self-referential selection bias",
            "No composite total",
            "标签必须能消失",
            "does not depend on transmitting the private repository",
        ):
            self.assertIn(snippet, methodology)

    def _assert_matching_tree(self, expected_dir: Path, actual_dir: Path) -> None:
        expected_files = sorted(
            path.relative_to(expected_dir)
            for path in expected_dir.rglob("*")
            if path.is_file()
        )
        actual_files = sorted(
            path.relative_to(actual_dir)
            for path in actual_dir.rglob("*")
            if path.is_file()
        )
        self.assertEqual(expected_files, actual_files)
        for relative_path in expected_files:
            self.assertEqual(
                (expected_dir / relative_path).read_text(encoding="utf-8"),
                (actual_dir / relative_path).read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
