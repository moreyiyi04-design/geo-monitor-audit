import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.compiler import (
    COMPILED_END_MARKER,
    COMPILED_START_MARKER,
    compile_readme,
    render_compiled_block,
    replace_compiled_block,
)


def envelope(value):
    return {"v": value, "src": ["e1"], "conf": "stated"}


class CompilerRenderingTests(unittest.TestCase):
    def test_render_compiled_block_keeps_discovery_pool_out_of_public_readme(self):
        # Break caught: the internal discovery pool is mistaken for a recommendation list.
        # Break caught: README omits the broad market-map layer even when a map file exists.
        profiles = [
            {
                "slug": "alpha",
                "name_cn": envelope("阿尔法"),
                "name_en": envelope("Alpha"),
                "market": "domestic",
                "category": ["监测/可见性追踪", "品牌监测"],
                "delivery_form": envelope("SaaS 面板"),
                "openness": "closed",
                "homepage": envelope("https://alpha.example"),
                "pricing": {"has_public_pricing": envelope(False)},
                "scores": {
                    "transparency": 5,
                    "verifiability": 4,
                    "lock_in_risk": 2,
                    "measurement_rigor": 3,
                    "oss_health": 1,
                },
                "risk_flags": [],
                "evidence": [{"id": "e1", "fetched_at": "2026-07-29"}],
            }
        ]
        market_map = [
            {
                "slug": "beta",
                "name": "贝塔 / Beta",
                "market": "overseas",
                "category": ["agent-skill/prompt-pack"],
                "delivery_form": "API",
                "openness": "open-source",
                "coverage": "market-map-only",
                "homepage": "https://beta.example",
            },
            {
                "slug": "alpha",
                "name": "阿尔法 / Alpha",
                "market": "domestic",
                "category": ["监测/可见性追踪", "品牌监测"],
                "delivery_form": "SaaS 面板",
                "openness": "closed",
                "coverage": "deep-profile",
                "homepage": "https://alpha.example",
            },
        ]

        block = render_compiled_block(profiles, market_map)

        self.assertIn("完整候选池保留在 wiki/market-map.json", block)
        self.assertNotIn("### 附录：全球市场地图", block)
        self.assertNotIn("| 阿尔法 / Alpha |", block)
        self.assertNotIn("| 贝塔 / Beta |", block)

    def test_render_compiled_block_omits_low_signal_profile_tables(self):
        # Break caught: raw scores and repeated risk labels overwhelm the decision report.
        profiles = [
            {
                "slug": "beta",
                "name_cn": envelope("贝塔"),
                "name_en": envelope("Beta"),
                "market": "overseas",
                "category": ["agent-skill/prompt-pack"],
                "delivery_form": envelope("API"),
                "openness": "open-source",
                "homepage": envelope("https://beta.example"),
                "pricing": {"has_public_pricing": envelope(True)},
                "scores": {
                    "transparency": 3,
                    "verifiability": 5,
                    "lock_in_risk": 4,
                    "measurement_rigor": 2,
                    "oss_health": 5,
                },
                "risk_flags": [],
                "evidence": [{"id": "e1", "fetched_at": "2026-07-30"}],
            },
            {
                "slug": "alpha",
                "name_cn": envelope("阿尔法"),
                "name_en": envelope("Alpha"),
                "market": "domestic",
                "category": ["监测/可见性追踪", "品牌监测"],
                "delivery_form": envelope("SaaS 面板"),
                "openness": "closed",
                "homepage": envelope("https://alpha.example"),
                "pricing": {"has_public_pricing": envelope(False)},
                "scores": {
                    "transparency": 5,
                    "verifiability": 4,
                    "lock_in_risk": 2,
                    "measurement_rigor": 3,
                    "oss_health": 1,
                },
                "risk_flags": [
                    {"flag": "年付起购", "tier": "orange", "origin": "auto", "src": ["e1"]},
                    {
                        "flag": "未披露每 prompt 采样次数",
                        "tier": "yellow",
                        "origin": "auto",
                        "src": ["e1"],
                    },
                ],
                "evidence": [{"id": "e1", "fetched_at": "2026-07-29"}],
            },
        ]

        block = render_compiled_block(profiles)

        self.assertEqual(
            """\
> 数据截至 2026-07-30
> 完整候选池保留在 wiki/market-map.json，仅供研究与审计，不构成公开推荐。""",
            block,
        )
        for removed_heading in (
            "### 选型矩阵",
            "### 分数",
            "### 产品档案表",
            "### 标签清单",
        ):
            self.assertNotIn(removed_heading, block)


class CompiledBlockReplacementTests(unittest.TestCase):
    def test_replace_compiled_block_preserves_handwritten_sections(self):
        # Break caught: replacing compiled bytes mutates the adjacent handwritten content.
        readme = """\
<!-- ARIS-GEO:HANDWRITTEN:START -->
Handwritten intro.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
Old bytes.
<!-- ARIS-GEO:COMPILED:END -->
"""

        updated = replace_compiled_block(readme, "Fresh block.\n")

        self.assertEqual(
            """\
<!-- ARIS-GEO:HANDWRITTEN:START -->
Handwritten intro.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
Fresh block.
<!-- ARIS-GEO:COMPILED:END -->
""",
            updated,
        )

    def test_replace_compiled_block_requires_start_marker(self):
        # Break caught: malformed README silently compiles without the required start marker.
        with self.assertRaisesRegex(
            ValueError,
            rf"missing compiled start marker: {COMPILED_START_MARKER}",
        ):
            replace_compiled_block("no markers here", "ignored")

    def test_replace_compiled_block_requires_end_marker(self):
        # Break caught: malformed README silently compiles without the required end marker.
        readme = f"{COMPILED_START_MARKER}\npartial block\n"

        with self.assertRaisesRegex(
            ValueError,
            rf"missing compiled end marker: {COMPILED_END_MARKER}",
        ):
            replace_compiled_block(readme, "ignored")

    def test_replace_compiled_block_rejects_duplicate_start_marker(self):
        # Break caught: duplicate compiled start markers let the compiler rewrite an ambiguous block.
        readme = """\
<!-- ARIS-GEO:COMPILED:START -->
first
<!-- ARIS-GEO:COMPILED:START -->
second
<!-- ARIS-GEO:COMPILED:END -->
"""

        with self.assertRaisesRegex(
            ValueError,
            rf"duplicate compiled start marker: {COMPILED_START_MARKER}",
        ):
            replace_compiled_block(readme, "ignored")

    def test_replace_compiled_block_rejects_duplicate_end_marker(self):
        # Break caught: duplicate compiled end markers let the compiler leave trailing stale bytes behind.
        readme = """\
<!-- ARIS-GEO:COMPILED:START -->
block
<!-- ARIS-GEO:COMPILED:END -->
<!-- ARIS-GEO:COMPILED:END -->
"""

        with self.assertRaisesRegex(
            ValueError,
            rf"duplicate compiled end marker: {COMPILED_END_MARKER}",
        ):
            replace_compiled_block(readme, "ignored")

    def test_replace_compiled_block_rejects_end_marker_before_start_marker(self):
        # Break caught: an end marker before the start marker still allows the compiler to rewrite bytes.
        readme = """\
<!-- ARIS-GEO:COMPILED:END -->
orphan
<!-- ARIS-GEO:COMPILED:START -->
block
"""

        with self.assertRaisesRegex(
            ValueError,
            "compiled end marker occurs before start marker",
        ):
            replace_compiled_block(readme, "ignored")


class CompileReadmeCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-compiler-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki" / "products").mkdir(parents=True)
        self.readme_path = self.repo_root / "README.md"
        # 指向本仓库自己的脚本。此前这里硬编码了 /private/tmp/aris-geo-build/... —— 某次
        # 本地构建目录的残留路径。该目录在 CI 上从不存在，于是这两个用例一直拿到
        # "can't open file" 而不是被测的错误信息，断言失败却被当成待修的行为问题。
        self.script_path = Path(__file__).resolve().parent.parent / "tools" / "compile_readme.py"
        self._write_profile(
            "beta",
            {
                "slug": "beta",
                "name_cn": envelope("贝塔"),
                "name_en": envelope("Beta"),
                "market": "overseas",
                "category": ["agent-skill/prompt-pack"],
                "delivery_form": envelope("API"),
                "openness": "open-source",
                "homepage": envelope("https://beta.example"),
                "pricing": {"has_public_pricing": envelope(True)},
                "scores": {
                    "transparency": 3,
                    "verifiability": 5,
                    "lock_in_risk": 4,
                    "measurement_rigor": 2,
                    "oss_health": 5,
                },
                "risk_flags": [],
                "evidence": [{"id": "e1", "fetched_at": "2026-07-30"}],
            },
        )
        self._write_profile(
            "alpha",
            {
                "slug": "alpha",
                "name_cn": envelope("阿尔法"),
                "name_en": envelope("Alpha"),
                "market": "domestic",
                "category": ["监测/可见性追踪"],
                "delivery_form": envelope("SaaS 面板"),
                "openness": "closed",
                "homepage": envelope("https://alpha.example"),
                "pricing": {"has_public_pricing": envelope(False)},
                "scores": {
                    "transparency": 5,
                    "verifiability": 4,
                    "lock_in_risk": 2,
                    "measurement_rigor": 3,
                    "oss_health": 1,
                },
                "risk_flags": [],
                "evidence": [{"id": "e1", "fetched_at": "2026-07-29"}],
            },
        )

    def _write_profile(self, slug, profile):
        profile_path = self.repo_root / "wiki" / "products" / f"{slug}.json"
        profile_path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _write_market_map(self, products):
        market_map_path = self.repo_root / "wiki" / "market-map.json"
        market_map_path.write_text(
            json.dumps({"products": products}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_check_mode_returns_nonzero_for_stale_compiled_content_without_rewriting(self):
        # Break caught: --check rewrites README or exits zero when compiled bytes are stale.
        original = """\
<!-- ARIS-GEO:HANDWRITTEN:START -->
Handwritten intro.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
stale bytes
<!-- ARIS-GEO:COMPILED:END -->
"""
        self.readme_path.write_text(original, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.script_path), "--check"],
            cwd=self.repo_root / "wiki",
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("README compiled block is stale", result.stderr)
        self.assertEqual(original, self.readme_path.read_text(encoding="utf-8"))

    def test_check_mode_rejects_malformed_compiled_markers_without_rewriting(self):
        # Break caught: --check normalizes malformed compiled markers instead of failing and preserving bytes.
        original = """\
<!-- ARIS-GEO:HANDWRITTEN:START -->
Handwritten intro.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:END -->
orphan
<!-- ARIS-GEO:COMPILED:START -->
stale bytes
"""
        self.readme_path.write_text(original, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.script_path), "--check"],
            cwd=self.repo_root / "wiki",
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("compiled end marker occurs before start marker", result.stderr)
        self.assertEqual(original, self.readme_path.read_text(encoding="utf-8"))

    def test_compile_readme_allows_missing_market_map_file(self):
        # Break caught: making the market map the only appendix breaks repos without one.
        self.readme_path.write_text(
            """\
<!-- ARIS-GEO:COMPILED:START -->
stale bytes
<!-- ARIS-GEO:COMPILED:END -->
""",
            encoding="utf-8",
        )

        _, compiled = compile_readme(self.repo_root)

        self.assertNotIn("### 附录：全球市场地图", compiled)
        self.assertIn("完整候选池保留在 wiki/market-map.json", compiled)

    def test_compile_readme_rejects_duplicate_market_map_slug(self):
        # Break caught: the market-map layer silently accepts ambiguous duplicate slugs.
        self.readme_path.write_text(
            """\
<!-- ARIS-GEO:COMPILED:START -->
stale bytes
<!-- ARIS-GEO:COMPILED:END -->
""",
            encoding="utf-8",
        )
        self._write_market_map(
            [
                {
                    "slug": "alpha",
                    "name": "阿尔法 / Alpha",
                    "market": "domestic",
                    "category": ["监测/可见性追踪"],
                    "delivery_form": "SaaS 面板",
                    "openness": "closed",
                    "coverage": "deep-profile",
                    "homepage": "https://alpha.example",
                },
                {
                    "slug": "alpha",
                    "name": "Alpha Duplicate",
                    "market": "overseas",
                    "category": ["agent-skill/prompt-pack"],
                    "delivery_form": "API",
                    "openness": "open-source",
                    "coverage": "market-map-only",
                    "homepage": "https://duplicate.example",
                },
            ]
        )

        with self.assertRaisesRegex(ValueError, "duplicate market-map slug: alpha"):
            compile_readme(self.repo_root)

    def test_compile_readme_rejects_invalid_market_map_coverage(self):
        # Break caught: the market-map layer accepts unsupported coverage labels and renders misleading output.
        self.readme_path.write_text(
            """\
<!-- ARIS-GEO:COMPILED:START -->
stale bytes
<!-- ARIS-GEO:COMPILED:END -->
""",
            encoding="utf-8",
        )
        self._write_market_map(
            [
                {
                    "slug": "alpha",
                    "name": "阿尔法 / Alpha",
                    "market": "domestic",
                    "category": ["监测/可见性追踪"],
                    "delivery_form": "SaaS 面板",
                    "openness": "closed",
                    "coverage": "unknown",
                    "homepage": "https://alpha.example",
                }
            ]
        )

        with self.assertRaisesRegex(
            ValueError,
            "invalid market-map coverage for alpha: unknown",
        ):
            compile_readme(self.repo_root)


if __name__ == "__main__":
    unittest.main()
