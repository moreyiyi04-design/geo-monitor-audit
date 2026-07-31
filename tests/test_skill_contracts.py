import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")

SKILL_EXPECTATIONS = {
    "geo-seed": {
        "description_fragment": "Use when",
        "must_contain": (
            "/geo-seed",
            "Inputs",
            "Outputs",
            "wiki/queue.json",
            "Allowed observations",
            "Must not",
        ),
    },
    "geo-plan-queries": {
        "description_fragment": "Use when",
        "must_contain": (
            "/geo-plan-queries",
            "Inputs",
            "Outputs",
            "queries.json",
            "Allowed observations",
            "Must not",
        ),
    },
    "geo-digest": {
        "description_fragment": "Use when",
        "must_contain": (
            "/geo-digest",
            "Inputs",
            "Outputs",
            "evidence.md",
            "Allowed observations",
            "Must not",
        ),
    },
    "geo-profile": {
        "description_fragment": "Use when",
        "must_contain": (
            "/geo-profile",
            "Inputs",
            "Outputs",
            "products/<slug>.json",
            "Allowed observations",
            "Must not",
        ),
    },
    "geo-review": {
        "description_fragment": "Use when",
        "must_contain": (
            "/geo-review --persona vendor --slug <slug>",
            "/geo-review --persona skeptic --slug <slug>",
            "/geo-review --persona arbiter --slug <slug>",
            "vendor",
            "skeptic",
            "arbiter",
            "vendor.json",
            "skeptic.json",
            "patch.json",
            "Allowed observations",
            "Must not",
        ),
    },
}

SHARED_DOCS = {
    "SCHEMA.md": ("conf", "unknowns[]", "scores", "risk_flags"),
    "EVIDENCE_RULES.md": ("paid_placement_suspected", "sha256", "fetched_at", "unknown"),
    "GRADING.md": ("A", "B", "C", "D", "E", "claimed_change_pp"),
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise AssertionError("missing opening frontmatter delimiter")
    try:
        closing_index = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError("missing closing frontmatter delimiter") from exc

    frontmatter: dict[str, str] = {}
    for raw_line in lines[1:closing_index]:
        if not raw_line.strip():
            continue
        key, separator, value = raw_line.partition(":")
        if separator != ":":
            raise AssertionError(f"invalid frontmatter line: {raw_line}")
        frontmatter[key.strip()] = value.strip()
    body = "\n".join(lines[closing_index + 1 :]).strip()
    return frontmatter, body


class SkillContractTests(unittest.TestCase):
    def test_skill_files_exist_and_match_contracts(self):
        for skill_name, expectation in SKILL_EXPECTATIONS.items():
            with self.subTest(skill=skill_name):
                path = SKILLS_ROOT / skill_name / "SKILL.md"
                self.assertTrue(path.is_file(), f"missing skill file: {path}")
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("[TODO", content)
                self.assertNotIn("TODO:", content)
                self.assertNotIn("placeholder", content.lower())

                frontmatter, body = parse_frontmatter(content)
                self.assertEqual({"name", "description"}, set(frontmatter))
                self.assertEqual(skill_name, frontmatter["name"])
                self.assertRegex(frontmatter["name"], NAME_PATTERN)
                self.assertTrue(
                    frontmatter["description"].startswith(expectation["description_fragment"]),
                    "description must start with 'Use when'",
                )
                self.assertNotIn("This skill", frontmatter["description"])
                self.assertNotIn("TODO", frontmatter["description"])
                self.assertTrue(body, "skill body must not be empty")

                for fragment in expectation["must_contain"]:
                    self.assertIn(fragment, body)

    def test_shared_reference_docs_exist_and_cover_required_terms(self):
        shared_root = SKILLS_ROOT / "shared"
        for filename, fragments in SHARED_DOCS.items():
            with self.subTest(filename=filename):
                path = shared_root / filename
                self.assertTrue(path.is_file(), f"missing shared doc: {path}")
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("[TODO", content)
                self.assertNotIn("placeholder", content.lower())
                for fragment in fragments:
                    self.assertIn(fragment, content)

    def test_geo_review_declares_persona_specific_visibility(self):
        content = (SKILLS_ROOT / "geo-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("vendor only sees", content)
        self.assertIn("skeptic only sees", content)
        self.assertIn("arbiter sees", content)
        self.assertIn("must not assume hidden files exist", content)


if __name__ == "__main__":
    unittest.main()
