from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.publication import build_publication


class PublicationBuilderTests(unittest.TestCase):
    def test_builds_hashed_evidence_profile_and_computed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            catalog = {
                "fetched_at": "2026-07-31",
                "products": [
                    {
                        "slug": "demo",
                        "name_cn": "演示",
                        "name_en": "Demo",
                        "homepage": "https://demo.example/",
                        "market": "overseas",
                        "category": ["监测/可见性追踪"],
                        "delivery_form": "SaaS",
                        "openness": "closed",
                        "vendor_domains": ["demo.example"],
                        "sources": [
                            {
                                "id": "e1",
                                "url": "https://demo.example/pricing",
                                "kind": "vendor_pricing_page",
                                "excerpt": "The Starter plan costs $29 per month.",
                            }
                        ],
                        "facts": {
                            "pricing.has_public_pricing": {
                                "v": True,
                                "src": ["e1"],
                                "conf": "stated",
                            },
                            "measurement.samples_per_prompt": {
                                "v": None,
                                "src": [],
                                "conf": "unknown",
                            },
                        },
                    }
                ],
            }

            profiles = build_publication(repo_root, catalog)

            self.assertEqual(["demo"], [profile["slug"] for profile in profiles])
            excerpt_path = repo_root / "wiki" / "raw" / "demo" / "e1.txt"
            self.assertEqual("The Starter plan costs $29 per month.\n", excerpt_path.read_text())
            profile = json.loads((repo_root / "wiki" / "products" / "demo.json").read_text())
            self.assertEqual(
                hashlib.sha256(excerpt_path.read_bytes()).hexdigest(),
                profile["evidence"][0]["sha256"],
            )
            self.assertIn("measurement.samples_per_prompt", profile["unknowns"])
            self.assertIn("pricing.refund_terms", profile["unknowns"])
            self.assertNotIn("pricing.has_public_pricing", profile["unknowns"])
            self.assertEqual(True, profile["pricing"]["has_public_pricing"]["v"])
            self.assertIn("scores", profile)
            self.assertIn("risk_flags", profile)
            self.assertEqual(
                ["demo"],
                json.loads((repo_root / "wiki" / "queue.json").read_text()),
            )
            sources = json.loads((repo_root / "wiki" / "sources.json").read_text())
            self.assertEqual("https://demo.example/pricing", sources["products"][0]["urls"][0]["url"])

    def test_rejects_duplicate_slugs_and_unknown_source_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            duplicate = {
                "fetched_at": "2026-07-31",
                "products": [
                    self._minimal_product("same"),
                    self._minimal_product("same"),
                ],
            }
            with self.assertRaisesRegex(ValueError, "duplicate product slug"):
                build_publication(repo_root, duplicate)

            missing_source = self._minimal_product("bad")
            missing_source["facts"] = {
                "pricing.has_public_pricing": {
                    "v": True,
                    "src": ["missing"],
                    "conf": "stated",
                }
            }
            with self.assertRaisesRegex(ValueError, "unknown source id"):
                build_publication(
                    repo_root,
                    {"fetched_at": "2026-07-31", "products": [missing_source]},
                )

    @staticmethod
    def _minimal_product(slug: str) -> dict[str, object]:
        return {
            "slug": slug,
            "name_cn": slug,
            "name_en": slug,
            "homepage": f"https://{slug}.example/",
            "market": "overseas",
            "category": ["监测/可见性追踪"],
            "delivery_form": "SaaS",
            "openness": "closed",
            "vendor_domains": [f"{slug}.example"],
            "sources": [
                {
                    "id": "e1",
                    "url": f"https://{slug}.example/",
                    "kind": "vendor_marketing",
                    "excerpt": slug,
                }
            ],
            "facts": {},
        }
