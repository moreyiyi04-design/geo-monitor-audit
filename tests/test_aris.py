import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.aris_geo.aris import DEFAULT_ALLOWED_TOOLS, ArisResult, parse_aris_result, run_aris_phase


def aris_payload(**overrides):
    payload = {
        "message": '{"ok":true}',
        "model": "deepseek-v4-flash",
        "iterations": 4,
        "auto_compaction": None,
        "tool_uses": ["Skill", "read_file", "write_file"],
        "tool_results": [{"tool": "read_file", "is_error": False, "content": "ok"}],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 3,
        },
    }
    payload.update(overrides)
    return payload


class ParseArisResultTests(unittest.TestCase):
    def test_parse_aris_result_rejects_invalid_json_stdout(self):
        # Break caught: malformed ARIS stdout is treated as a successful phase result.
        with self.assertRaisesRegex(ValueError, "invalid ARIS JSON"):
            parse_aris_result("{not json")

    def test_parse_aris_result_rejects_auto_compaction(self):
        # Break caught: compacted transcripts are accepted despite the design treating them as tainted.
        stdout = json.dumps(
            aris_payload(auto_compaction={"removed_messages": 2, "notice": "compacted"}),
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(ValueError, "auto-compaction"):
            parse_aris_result(stdout)

    def test_parse_aris_result_rejects_denied_permission_results(self):
        # Break caught: denied tool calls continue the turn and still get accepted as valid output.
        stdout = json.dumps(
            aris_payload(
                tool_results=[
                    {
                        "tool": "write_file",
                        "is_error": True,
                        "content": [{"type": "text", "text": "Permission denied by policy"}],
                    }
                ]
            ),
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(ValueError, "permission-denied tool result"):
            parse_aris_result(stdout)

    def test_parse_aris_result_allows_successful_content_that_mentions_permission_denied(self):
        # Break caught: successful file content that quotes denial text is falsely rejected as a denied tool result.
        stdout = json.dumps(
            aris_payload(
                tool_results=[
                    {
                        "tool": "read_file",
                        "is_error": False,
                        "content": "Log excerpt: permission denied on a previous host.",
                    }
                ]
            ),
            ensure_ascii=False,
        )

        result = parse_aris_result(stdout)

        self.assertEqual(
            "Log excerpt: permission denied on a previous host.",
            result.tool_results[0]["content"],
        )

    def test_parse_aris_result_rejects_structured_deny_status_without_free_text_scan(self):
        # Break caught: deny-shaped tool results are missed unless the parser happens to substring-match human text.
        stdout = json.dumps(
            aris_payload(
                tool_results=[
                    {
                        "tool": "write_file",
                        "status": "denied",
                        "permission": "workspace-write",
                        "content": "noisy payload that should not matter",
                    }
                ]
            ),
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(ValueError, "permission-denied tool result"):
            parse_aris_result(stdout)

    def test_parse_aris_result_rejects_structured_error_field_with_denied_payload(self):
        # Break caught: explicit error payloads with deny metadata pass unless the parser inspects error-shaped fields.
        stdout = json.dumps(
            aris_payload(
                tool_results=[
                    {
                        "tool": "write_file",
                        "is_error": True,
                        "error": {
                            "type": "permission_denied",
                            "message": "write_file refused",
                        },
                        "content": "ordinary content field",
                    }
                ]
            ),
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(ValueError, "permission-denied tool result"):
            parse_aris_result(stdout)

    def test_parse_aris_result_rejects_excessive_iterations(self):
        # Break caught: a looping ARIS turn is treated as successful instead of failing fast.
        stdout = json.dumps(aris_payload(iterations=9), ensure_ascii=False)

        with self.assertRaisesRegex(ValueError, "iterations exceed 8"):
            parse_aris_result(stdout)

    def test_parse_aris_result_requires_declared_tools(self):
        # Break caught: phases that never read staged files still pass contract validation.
        stdout = json.dumps(aris_payload(tool_uses=["Skill", "write_file"]), ensure_ascii=False)

        with self.assertRaisesRegex(ValueError, "missing required tool: read_file"):
            parse_aris_result(stdout, required_tools=("read_file",))

    def test_parse_aris_result_returns_structured_result_for_valid_payload(self):
        # Break caught: valid ARIS JSON cannot be consumed as a typed result contract.
        result = parse_aris_result(
            json.dumps(aris_payload(), ensure_ascii=False),
            required_tools=("read_file",),
        )

        self.assertIsInstance(result, ArisResult)
        self.assertEqual('{"ok":true}', result.message)
        self.assertEqual("deepseek-v4-flash", result.model)
        self.assertEqual(4, result.iterations)
        self.assertEqual(["Skill", "read_file", "write_file"], result.tool_uses)
        self.assertEqual(3, result.usage["cache_read_input_tokens"])

    def test_parse_aris_result_requires_numeric_usage_fields(self):
        # Break caught: control-signal usage fields accept missing, bool, negative, or non-numeric values.
        bad_cases = [
            ({}, "missing usage field: input_tokens"),
            ({"input_tokens": True}, "usage field input_tokens must be a non-bool number"),
            ({"input_tokens": -1}, "usage field input_tokens must be non-negative"),
            ({"cache_read_input_tokens": "3"}, "usage field cache_read_input_tokens must be a non-bool number"),
        ]

        for patch, message in bad_cases:
            with self.subTest(patch=patch):
                usage = dict(aris_payload()["usage"])
                usage.update(patch)
                if patch == {}:
                    usage.pop("input_tokens")
                stdout = json.dumps(aris_payload(usage=usage), ensure_ascii=False)
                with self.assertRaisesRegex(ValueError, message):
                    parse_aris_result(stdout)


class RunArisPhaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-aris-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.cwd = self.tempdir / "inbox-vendor"
        self.cwd.mkdir()

    def test_run_aris_phase_uses_prompt_subcommand_workspace_write_allowed_tools_and_cwd(self):
        # Break caught: the driver uses the wrong CLI form or omits the sandbox/tool contract.
        seen = {}

        def fake_runner(argv, **kwargs):
            seen["argv"] = argv
            seen["kwargs"] = kwargs
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(aris_payload(), ensure_ascii=False),
                stderr="",
            )

        result = run_aris_phase(
            prompt="/geo-review --persona vendor --slug demo",
            model="deepseek-v4-flash",
            cwd=self.cwd,
            runner=fake_runner,
            required_tools=("read_file",),
        )

        self.assertIsInstance(result, ArisResult)
        self.assertEqual(
            [
                "aris",
                "--print",
                "--output-format",
                "json",
                "--model",
                "deepseek-v4-flash",
                "--permission-mode",
                "workspace-write",
                "--allowedTools",
                ",".join(DEFAULT_ALLOWED_TOOLS),
                "--cwd",
                str(self.cwd),
                "prompt",
                "/geo-review --persona vendor --slug demo",
            ],
            seen["argv"],
        )
        self.assertEqual("", seen["kwargs"]["input"])
        self.assertTrue(seen["kwargs"]["text"])
        self.assertFalse(seen["kwargs"]["check"])
        self.assertEqual(str(self.cwd), seen["kwargs"]["cwd"])

    def test_run_aris_phase_rejects_non_zero_exit(self):
        # Break caught: failed ARIS executions continue into JSON parsing as if the phase succeeded.
        def fake_runner(argv, **kwargs):
            return SimpleNamespace(returncode=17, stdout="", stderr="boom")

        with self.assertRaisesRegex(ValueError, "ARIS exited with code 17"):
            run_aris_phase(
                prompt="/geo-review --persona vendor --slug demo",
                model="deepseek-v4-flash",
                cwd=self.cwd,
                runner=fake_runner,
            )


if __name__ == "__main__":
    unittest.main()
