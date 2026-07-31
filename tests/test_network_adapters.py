import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.github import GitHubHealthClient
from tools.aris_geo.http import HttpRequest, HttpResponse, canonical_request_sha256
from tools.aris_geo.tavily import TavilyClient


def json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


class CanonicalRequestTests(unittest.TestCase):
    def test_canonical_request_sha256_ignores_authorization_and_normalizes_json(self):
        # Break caught: cache keys change with bearer tokens or JSON field ordering.
        first = HttpRequest(
            method="POST",
            url="https://api.tavily.com/search",
            headers={
                "Authorization": "Bearer secret-one",
                "Content-Type": "application/json",
                "X-Trace": "same",
            },
            body=b'{"query":"geo","max_results":5}',
        )
        second = HttpRequest(
            method="post",
            url="https://api.tavily.com/search",
            headers={
                "authorization": "Bearer secret-two",
                "content-type": "application/json",
                "x-trace": "same",
            },
            body=b'{ "max_results": 5, "query": "geo" }',
        )

        self.assertEqual(canonical_request_sha256(first), canonical_request_sha256(second))


class TavilyClientTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-network-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.cache_dir = self.tempdir / "cache"
        self.snapshot_path = self.tempdir / "wiki" / "raw" / "demo" / "tavily-search.json"

    def test_search_uses_cache_hit_without_credentials_or_transport(self):
        # Break caught: cached responses still require a live API key or perform network I/O.
        client = TavilyClient(self.cache_dir, api_key=None, transport=self._unexpected_transport)
        request = client.build_request("geo monitoring", max_results=3)
        cache_key = canonical_request_sha256(request)
        payload = {
            "fetched_at": "2026-07-31T10:00:00Z",
            "sha256": hashlib.sha256(json_bytes({"results": [{"url": "https://example.com"}]})).hexdigest(),
            "content": {"results": [{"url": "https://example.com"}]},
        }
        (self.cache_dir / f"{cache_key}.json").parent.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / f"{cache_key}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        result = client.search("geo monitoring", max_results=3)

        self.assertEqual({"results": [{"url": "https://example.com"}]}, result)

    def test_search_writes_atomic_cache_and_snapshot_with_hash_metadata(self):
        # Break caught: live Tavily fetches do not persist reproducible snapshot metadata.
        seen = []

        def transport(request):
            seen.append(request)
            return HttpResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body=json_bytes({"results": [{"url": "https://example.com/a", "content": "A"}]}),
            )

        client = TavilyClient(
            self.cache_dir,
            api_key="secret-token",
            transport=transport,
            clock=lambda: "2026-07-31T11:15:00Z",
        )

        result = client.search("geo monitoring", max_results=1, snapshot_path=self.snapshot_path)

        self.assertEqual({"results": [{"url": "https://example.com/a", "content": "A"}]}, result)
        self.assertEqual(1, len(seen))
        snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        expected_hash = hashlib.sha256(json_bytes(result)).hexdigest()
        self.assertEqual("2026-07-31T11:15:00Z", snapshot["fetched_at"])
        self.assertEqual(expected_hash, snapshot["sha256"])
        self.assertEqual(result, snapshot["content"])
        request = client.build_request("geo monitoring", max_results=1)
        self.assertTrue((self.cache_dir / f"{canonical_request_sha256(request)}.json").is_file())
        self.assertNotIn("secret-token", self.snapshot_path.read_text(encoding="utf-8"))

    def test_search_rejects_http_errors_without_caching_or_token_leak(self):
        # Break caught: failed Tavily responses get cached or leak credentials through error text.
        def transport(_request):
            return HttpResponse(
                status=401,
                headers={"Content-Type": "application/json"},
                body=json_bytes({"error": "denied"}),
            )

        client = TavilyClient(self.cache_dir, api_key="secret-token", transport=transport)

        with self.assertRaisesRegex(RuntimeError, "Tavily request failed with HTTP 401") as ctx:
            client.search("geo monitoring")

        self.assertNotIn("secret-token", str(ctx.exception))
        self.assertFalse(self.cache_dir.exists() and any(self.cache_dir.iterdir()))
        self.assertFalse(self.snapshot_path.exists())

    def test_search_rejects_invalid_json_shape_without_caching(self):
        # Break caught: malformed Tavily payloads are cached as if they were valid evidence.
        def transport(_request):
            return HttpResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body=json_bytes({"answer": "missing results"}),
            )

        client = TavilyClient(self.cache_dir, api_key="secret-token", transport=transport)

        with self.assertRaisesRegex(ValueError, "Tavily response must contain a results list"):
            client.search("geo monitoring")

        self.assertFalse(self.cache_dir.exists() and any(self.cache_dir.iterdir()))

    @staticmethod
    def _unexpected_transport(_request):
        raise AssertionError("transport should not be called on cache hit")


class GitHubHealthClientTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-gh-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.cache_dir = self.tempdir / "cache"

    def test_repository_health_returns_category_neutral_raw_metrics(self):
        # Break caught: the GitHub adapter bakes scoring policy into the live client instead of returning raw metrics.
        calls = []

        def transport(request):
            calls.append(request.url)
            if request.url.endswith("/repos/openai/codex"):
                return HttpResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json_bytes(
                        {
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
                    ),
                )
            if "/contributors" in request.url:
                return HttpResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json_bytes([{"login": "a"}, {"login": "b"}, {"login": "c"}]),
                )
            if "/commits" in request.url:
                return HttpResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json_bytes([{"sha": "1"}, {"sha": "2"}]),
                )
            if "/releases" in request.url:
                return HttpResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json_bytes(
                        [
                            {"tag_name": "v1.2.0", "published_at": "2026-07-01T00:00:00Z"},
                            {"tag_name": "v1.1.0", "published_at": "2026-06-01T00:00:00Z"},
                        ]
                    ),
                )
            raise AssertionError(f"unexpected URL {request.url}")

        client = GitHubHealthClient(self.cache_dir, token="super-secret", transport=transport)

        result = client.repository_health("openai", "codex")

        self.assertEqual(
            {
                "full_name": "openai/codex",
                "html_url": "https://github.com/openai/codex",
                "description": "CLI agent",
                "topics": ["ai", "cli"],
                "archived": False,
                "fork": False,
                "stars": 120,
                "watchers": 120,
                "forks": 10,
                "open_issues": 5,
                "subscribers": 7,
                "network_count": 11,
                "size_kb": 2048,
                "default_branch": "main",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2026-07-30T00:00:00Z",
                "pushed_at": "2026-07-30T12:00:00Z",
                "license_spdx": "MIT",
                "license_absent": False,
                "contributors_12mo": 3,
                "commits_90d": 2,
                "releases": 2,
                "last_release": "2026-07-01T00:00:00Z",
            },
            result,
        )
        self.assertEqual(4, len(calls))

    def test_repository_health_rejects_invalid_repo_shape_without_caching(self):
        # Break caught: malformed GitHub repo payloads are accepted and cached as valid health data.
        def transport(request):
            if request.url.endswith("/repos/openai/codex"):
                return HttpResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json_bytes({"stargazers_count": 120}),
                )
            raise AssertionError(f"unexpected URL {request.url}")

        client = GitHubHealthClient(self.cache_dir, token="super-secret", transport=transport)

        with self.assertRaisesRegex(ValueError, "GitHub repository response missing required field: full_name"):
            client.repository_health("openai", "codex")

        self.assertFalse(self.cache_dir.exists() and any(self.cache_dir.iterdir()))


if __name__ == "__main__":
    unittest.main()
