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
    render_compiled_block,
    replace_compiled_block,
)


def envelope(value):
    return {"v": value, "src": ["e1"], "conf": "stated"}


class CompilerRenderingTests(unittest.TestCase):
    def test_render_compiled_block_sorts_profiles_and_flags_deterministically(self):
        # Break caught: README bytes depend on input order instead of stable profile/flag sorting.
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
> 「未披露」≠「没有」；下表仅呈现已公开且有证据的字段。

### 选型矩阵
| 产品 | slug | 市场 | 形态 | 开放性 | 核心类别 |
| --- | --- | --- | --- | --- | --- |
| 阿尔法 / Alpha | alpha | domestic | SaaS 面板 | closed | 监测/可见性追踪 |
| 贝塔 / Beta | beta | overseas | API | open-source | agent-skill/prompt-pack |

### 分数
| 产品 | transparency | verifiability | lock_in_risk | measurement_rigor | oss_health |
| --- | --- | --- | --- | --- | --- |
| 阿尔法 / Alpha | 5 | 4 | 2 | 3 | 1 |
| 贝塔 / Beta | 3 | 5 | 4 | 2 | 5 |

### 产品档案表
| 产品 | 官网 | 类别 | 公开定价 |
| --- | --- | --- | --- |
| 阿尔法 / Alpha | https://alpha.example | 监测/可见性追踪, 品牌监测 | 未公开 |
| 贝塔 / Beta | https://beta.example | agent-skill/prompt-pack | 已公开 |

### 标签清单
#### 阿尔法 / Alpha
- 🟡 未披露每 prompt 采样次数
- 🟠 年付起购

#### 贝塔 / Beta
- 无
""",
            block,
        )


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


class CompileReadmeCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-compiler-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki" / "products").mkdir(parents=True)
        self.readme_path = self.repo_root / "README.md"
        self.script_path = Path("/private/tmp/aris-geo-build/tools/compile_readme.py")
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


if __name__ == "__main__":
    unittest.main()
