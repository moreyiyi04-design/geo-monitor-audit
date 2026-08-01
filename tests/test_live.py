import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.aris_geo.http import HttpResponse
from tools.aris_geo.live import build_live_phase_handlers
from tools.aris_geo.loop import GeoLoop


def json_text(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


class LivePhasePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-live-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki").mkdir(parents=True)
        (self.repo_root / "wiki" / "queue.json").write_text('["demo"]', encoding="utf-8")
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "bootstrap.txt").write_text(
            "bootstrap\n",
            encoding="utf-8",
        )
        (self.repo_root / "README.md").write_text(
            "<!-- ARIS-GEO:HANDWRITTEN:START -->\n"
            "handwritten\n"
            "<!-- ARIS-GEO:HANDWRITTEN:END -->\n\n"
            "<!-- ARIS-GEO:COMPILED:START -->\nold\n<!-- ARIS-GEO:COMPILED:END -->\n",
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "sources.json").write_text(
            json_text(
                {
                    "products": [
                        {
                            "slug": "demo",
                            "name": "Demo Product",
                            "market": "overseas",
                            "category": ["监测/可见性追踪"],
                            "openness": "closed",
                            "urls": [
                                {"url": "https://vendor.example/pricing", "kind": "vendor_pricing_page"},
                                {"url": "https://vendor.example/methodology", "kind": "methodology_doc"},
                            ],
                            "repo": "openai/codex",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_live_pipeline_uses_sources_manifest_direct_url_fallback_and_persona_isolation(self):
        # Break caught: live mode cannot run without Tavily, leaks persona files, or fails to apply deterministic review patches.
        seen_prompts = []
        seen_cwds = {}

        def fake_runner(argv, **kwargs):
            prompt = argv[-1]
            cwd = Path(kwargs["cwd"])
            seen_prompts.append(prompt)
            seen_cwds[prompt] = sorted(path.name for path in cwd.iterdir())

            if prompt == "/geo-plan-queries --slug demo":
                self.assertEqual(["seed.json"], seen_cwds[prompt])
                cwd.joinpath("queries.json").write_text(
                    json_text(
                        [
                            {"query": "Demo Product pricing", "kind": "vendor_pricing_page"},
                            {"query": "Demo Product methodology", "kind": "methodology_doc"},
                        ]
                    ),
                    encoding="utf-8",
                )
            elif prompt == "/geo-digest --slug demo":
                self.assertIn("evidence_inputs.json", seen_cwds[prompt])
                self.assertTrue(any(name.endswith(".txt") for name in seen_cwds[prompt]))
                cwd.joinpath("evidence.md").write_text("# Evidence digest\n", encoding="utf-8")
            elif prompt == "/geo-profile --slug demo":
                self.assertEqual(["evidence.md", "evidence_inputs.json", "seed.json"], seen_cwds[prompt])
                cwd.joinpath("demo.json").write_text(
                    json_text(
                        {
                            "schema_version": "v1",
                            "slug": "demo",
                            "name_cn": {"v": "演示产品", "src": ["e1"], "conf": "stated"},
                            "name_en": {"v": "Demo Product", "src": ["e1"], "conf": "stated"},
                            "homepage": {"v": "https://vendor.example", "src": ["e1"], "conf": "stated"},
                            "vendor_domains": ["vendor.example"],
                            "market": "overseas",
                            "category": ["监测/可见性追踪"],
                            "delivery_form": {"v": "SaaS", "src": ["e1"], "conf": "stated"},
                            "openness": "closed",
                            "measurement": {
                                "capture_channel": {"v": "browser", "src": ["e2"], "conf": "stated"},
                                "samples_per_prompt": {"v": 3, "src": ["e2"], "conf": "stated"},
                                "reports_confidence_interval": {"v": True, "src": ["e2"], "conf": "stated"},
                                "declares_noise_floor": {"v": True, "src": ["e2"], "conf": "stated"},
                                "model_version_pinning": {"v": True, "src": ["e2"], "conf": "stated"},
                                "sov_formula_public": {"v": True, "src": ["e2"], "conf": "stated"},
                            },
                            "mechanism": {
                                "data_source": {"v": "browser panels", "src": ["e2"], "conf": "stated"}
                            },
                            "pricing": {
                                "has_public_pricing": {"v": True, "src": ["e1"], "conf": "stated"},
                                "entry_engines": {"v": 2, "src": ["e1"], "conf": "stated"},
                                "entry_seats": {"v": 2, "src": ["e1"], "conf": "stated"},
                                "entry_prompts": {"v": 400, "src": ["e1"], "conf": "stated"},
                                "min_commit": {"v": "3 months", "src": ["e1"], "conf": "stated"},
                                "annual_only": {"v": False, "src": ["e1"], "conf": "stated"},
                                "trial": {"v": True, "src": ["e1"], "conf": "stated"},
                                "refund_terms": {"v": "公开", "src": ["e1"], "conf": "stated"},
                                "unit_inflation_risk": {"v": False, "src": ["e1"], "conf": "stated"},
                            },
                            "entity": {
                                "registry_verifiable": {"v": True, "src": ["e3"], "conf": "stated"},
                                "team_public": {"v": True, "src": ["e3"], "conf": "stated"},
                            },
                            "exit": {
                                "data_export": {"v": True, "src": ["e1"], "conf": "stated"},
                                "history_portable": {"v": True, "src": ["e1"], "conf": "stated"},
                                "content_hosted_by_vendor": {"v": False, "src": ["e1"], "conf": "stated"},
                                "contract_lock": {"v": "3 months", "src": ["e1"], "conf": "stated"},
                            },
                            "academic_anchor": {
                                "peer_reviewed": {"v": False, "src": ["e2"], "conf": "stated"},
                                "reproducible_experiments": {"v": False, "src": ["e2"], "conf": "stated"},
                                "benchmark": {"v": False, "src": ["e2"], "conf": "stated"},
                            },
                            "effect_claims": [
                                {
                                    "claim": "Methodology note claimed a 6% lift over 90 days.",
                                    "has_number": True,
                                    "has_denominator": False,
                                    "has_timeframe": True,
                                    "engine": "SearchGPT",
                                    "claimed_change_pp": 6.0,
                                    "grade_final": "C",
                                    "src": ["e2"],
                                }
                            ],
                            "evidence": [
                                {
                                    "id": "e1",
                                    "url": "https://vendor.example/pricing",
                                    "kind": "vendor_pricing_page",
                                    "fetched_at": "2026-07-31",
                                    "sha256": "placeholder",
                                    "excerpt_path": "wiki/raw/demo/e1.txt",
                                    "paid_placement_suspected": False,
                                },
                                {
                                    "id": "e2",
                                    "url": "https://vendor.example/methodology",
                                    "kind": "methodology_doc",
                                    "fetched_at": "2026-07-31",
                                    "sha256": "placeholder",
                                    "excerpt_path": "wiki/raw/demo/e2.txt",
                                    "paid_placement_suspected": False,
                                },
                                {
                                    "id": "e3",
                                    "url": "https://github.com/openai/codex",
                                    "kind": "repo",
                                    "fetched_at": "2026-07-31",
                                    "sha256": "placeholder",
                                    "excerpt_path": "wiki/raw/demo/e3.txt",
                                    "paid_placement_suspected": False,
                                },
                            ],
                            "case_studies": [],
                            "unknowns": [],
                        }
                    ),
                    encoding="utf-8",
                )
            elif prompt == "/geo-review --persona vendor --slug demo":
                self.assertEqual(["demo.json", "evidence.md"], seen_cwds[prompt])
                cwd.joinpath("vendor.json").write_text(
                    json_text({"support": "pricing stays sourced"}),
                    encoding="utf-8",
                )
            elif prompt == "/geo-review --persona skeptic --slug demo":
                self.assertEqual(["demo.json", "evidence.md"], seen_cwds[prompt])
                cwd.joinpath("skeptic.json").write_text(
                    json_text({"challenge": "adjust pricing visibility"}),
                    encoding="utf-8",
                )
            elif prompt == "/geo-review --persona arbiter --slug demo":
                self.assertEqual(["evidence.md", "skeptic.json", "vendor.json"], seen_cwds[prompt])
                cwd.joinpath("patch.json").write_text(
                    json_text(
                        {
                            "patch": [
                                {
                                    "op": "set",
                                    "field": "pricing.has_public_pricing",
                                    "value": {"v": False, "src": ["e1"], "conf": "stated"},
                                }
                            ],
                            "unresolved": [{"field": "pricing.has_public_pricing"}],
                        }
                    ),
                    encoding="utf-8",
                )
            else:
                raise AssertionError(f"unexpected prompt {prompt}")

            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "message": "{\"ok\":true}",
                        "model": "deepseek-v4-flash",
                        "iterations": 2,
                        "auto_compaction": None,
                        "tool_uses": ["Skill", "read_file", "write_file"],
                        "tool_results": [{"tool": "read_file", "is_error": False, "content": "ok"}],
                        "usage": {
                            "input_tokens": 11,
                            "output_tokens": 7,
                            "cache_creation_input_tokens": 0,
                            "cache_read_input_tokens": 1,
                        },
                    },
                    ensure_ascii=False,
                ),
                stderr="",
            )

        def direct_transport(request):
            body = {
                "https://vendor.example/pricing": b"Pricing excerpt",
                "https://vendor.example/methodology": b"Methodology excerpt",
            }[request.url]
            return HttpResponse(status=200, headers={"Content-Type": "text/plain"}, body=body)

        def github_transport(request):
            if request.url.endswith("/repos/openai/codex"):
                payload = {
                    "full_name": "openai/codex",
                    "html_url": "https://github.com/openai/codex",
                    "description": "CLI agent",
                    "topics": ["ai", "cli"],
                    "archived": False,
                    "fork": False,
                    "stargazers_count": 120,
                    "watchers_count": 120,
                    "forks_count": 10,
                    "open_issues_count": 5,
                    "subscribers_count": 7,
                    "network_count": 11,
                    "size": 2048,
                    "default_branch": "main",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2026-07-30T00:00:00Z",
                    "pushed_at": "2026-07-30T12:00:00Z",
                    "license": {"spdx_id": "MIT"},
                }
            elif "/contributors" in request.url:
                payload = [{"login": "a"}, {"login": "b"}, {"login": "c"}]
            elif "/commits" in request.url:
                payload = [{"sha": "1"}, {"sha": "2"}]
            elif "/releases" in request.url:
                payload = [{"tag_name": "v1.0.0", "published_at": "2026-07-01T00:00:00Z"}]
            else:
                raise AssertionError(f"unexpected GitHub URL {request.url}")
            return HttpResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )

        handlers = build_live_phase_handlers(
            self.repo_root,
            config_path=self.repo_root / "wiki" / "sources.json",
            model="deepseek-v4-flash",
            aris_bin="aris",
            runner=fake_runner,
            tavily_api_key=None,
            github_token="github-secret",
            direct_transport=direct_transport,
            github_transport=github_transport,
            clock=lambda: "2026-07-31T12:00:00Z",
        )

        outcome = GeoLoop(self.repo_root, phase_handlers=handlers).run_product("demo")

        self.assertEqual("passed", outcome.status)
        self.assertEqual(108, outcome.tokens)
        profile = json.loads((self.repo_root / "wiki" / "products" / "demo.json").read_text(encoding="utf-8"))
        self.assertFalse(profile["pricing"]["has_public_pricing"]["v"])
        self.assertEqual([{"field": "pricing.has_public_pricing"}], profile["unresolved"])
        self.assertEqual(0, profile["scores"]["oss_health"])
        self.assertTrue((self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").is_file())
        self.assertTrue((self.repo_root / "wiki" / "review" / "demo" / "vendor.json").is_file())
        self.assertTrue((self.repo_root / "wiki" / "review" / "demo" / "skeptic.json").is_file())
        self.assertIn("/geo-plan-queries --slug demo", seen_prompts)
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Demo Product", readme)
        self.assertNotIn("### 产品档案表", readme)

    def test_build_live_phase_handlers_rejects_apply_patch_outside_allowlist(self):
        # Break caught: arbiter patches can overwrite computed fields or arbitrary roots.
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "products").mkdir(parents=True)
        (self.repo_root / "wiki" / "review" / "demo").mkdir(parents=True)
        (self.repo_root / "wiki" / "products" / "demo.json").write_text(
            json_text(
                {
                    "schema_version": "v1",
                    "slug": "demo",
                    "market": "overseas",
                    "category": ["监测/可见性追踪"],
                    "openness": "closed",
                    "pricing": {"has_public_pricing": {"v": True, "src": ["e1"], "conf": "stated"}},
                    "scores": {"transparency": 5},
                    "unknowns": [],
                }
            ),
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "review" / "demo" / "patch.json").write_text(
            json_text(
                {
                    "patch": [
                        {
                            "op": "set",
                            "field": "scores.transparency",
                            "value": 0,
                        }
                    ],
                    "unresolved": [],
                }
            ),
            encoding="utf-8",
        )

        handlers = build_live_phase_handlers(
            self.repo_root,
            config_path=self.repo_root / "wiki" / "sources.json",
            model="deepseek-v4-flash",
            runner=lambda *_args, **_kwargs: None,
            direct_transport=lambda _request: None,
            github_transport=lambda _request: None,
        )

        outcome = handlers[next(iter([key for key in handlers if key.value == "apply"]))](
            "demo",
            SimpleNamespace(slug="demo"),
        )

        self.assertFalse(outcome.success)
        self.assertIn("patch field is not allowed", outcome.error)

    def test_build_live_phase_handlers_requires_direct_urls_when_tavily_is_unavailable(self):
        # Break caught: fetch pretends live evidence exists even when neither Tavily nor direct URLs are usable.
        (self.repo_root / "wiki" / "sources.json").write_text(
            json_text(
                {
                    "products": [
                        {
                            "slug": "demo",
                            "name": "Demo Product",
                            "market": "overseas",
                            "category": ["监测/可见性追踪"],
                            "openness": "closed",
                            "urls": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "queries.json").write_text("[]", encoding="utf-8")

        handlers = build_live_phase_handlers(
            self.repo_root,
            config_path=self.repo_root / "wiki" / "sources.json",
            model="deepseek-v4-flash",
            tavily_api_key=None,
            github_token=None,
            direct_transport=lambda _request: None,
            github_transport=lambda _request: None,
        )

        outcome = handlers[next(iter([key for key in handlers if key.value == "fetch"]))](
            "demo",
            SimpleNamespace(slug="demo"),
        )

        self.assertFalse(outcome.success)
        self.assertIn("no direct urls configured and Tavily API key is absent", outcome.error)


if __name__ == "__main__":
    unittest.main()
