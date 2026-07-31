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

    def test_canonical_request_sha256_redacts_url_userinfo_sensitive_query_keys_and_sensitive_headers(self):
        # Break caught: credential-bearing URL parts and headers leak into cache-key material.
        first = HttpRequest(
            method="GET",
            url=(
                "https://user-one:secret-one@example.com/search?"
                "query=geo&api_key=secret-a&TOKEN=secret-b&public=1"
            ),
            headers={
                "X-API-Key": "secret-header-a",
                "Cookie": "session=secret-cookie-a",
                "X-Trace": "same",
            },
        )
        second = HttpRequest(
            method="GET",
            url=(
                "https://user-two:secret-two@example.com/search?"
                "query=geo&api_key=secret-c&TOKEN=secret-d&public=1"
            ),
            headers={
                "Api-Key": "secret-header-b",
                "Set-Cookie": "session=secret-cookie-b",
                "X-Trace": "same",
            },
        )

        self.assertEqual(canonical_request_sha256(first), canonical_request_sha256(second))

    def test_canonical_request_sha256_still_distinguishes_non_secret_query_and_headers(self):
        # Break caught: over-redaction collapses distinct non-secret requests onto one cache key.
        first = HttpRequest(
            method="GET",
            url="https://example.com/search?query=geo&public=1",
            headers={"X-Trace": "same", "Accept": "application/json"},
        )
        second = HttpRequest(
            method="GET",
            url="https://example.com/search?query=geo&public=2",
            headers={"X-Trace": "same", "Accept": "application/json"},
        )
        third = HttpRequest(
            method="GET",
            url="https://example.com/search?query=geo&public=1",
            headers={"X-Trace": "different", "Accept": "application/json"},
        )

        self.assertNotEqual(canonical_request_sha256(first), canonical_request_sha256(second))
        self.assertNotEqual(canonical_request_sha256(first), canonical_request_sha256(third))


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

    def test_repository_health_uses_aggregate_cache_hit_without_token_transport_or_clock_sensitive_key(self):
        # Break caught: a warmed repo-health cache misses later because the key depends on moving request timestamps.
        calls = []

        def transport(_request):
            calls.append("called")
            raise AssertionError("transport should not be called on aggregate cache hit")

        warmer = GitHubHealthClient(
            self.cache_dir,
            token="super-secret",
            transport=self._github_transport,
            clock=lambda: "2026-07-31T10:00:00Z",
        )
        expected = warmer.repository_health("OpenAI", "Codex")

        reader = GitHubHealthClient(
            self.cache_dir,
            token=None,
            transport=transport,
            clock=lambda: "2026-08-01T10:00:00Z",
        )
        result = reader.repository_health("openai", "codex")

        self.assertEqual(expected, result)
        self.assertEqual([], calls)

    def test_repository_health_requires_token_on_aggregate_cache_miss_before_transport(self):
        # Break caught: GitHub live collection attempts transport even though a cache miss has no usable credentials.
        calls = []

        def transport(_request):
            calls.append("called")
            raise AssertionError("transport should not be called before token validation")

        client = GitHubHealthClient(self.cache_dir, token="", transport=transport)

        with self.assertRaisesRegex(ValueError, "GitHub token required for live request"):
            client.repository_health("openai", "codex")

        self.assertEqual([], calls)

    def test_repository_health_ignores_tampered_aggregate_cache_and_refetches_with_token(self):
        # Break caught: invalid aggregate repo-health snapshots are trusted instead of being replaced from live data.
        warmer = GitHubHealthClient(
            self.cache_dir,
            token="super-secret",
            transport=self._github_transport,
            clock=lambda: "2026-07-31T10:00:00Z",
        )
        expected = warmer.repository_health("openai", "codex")
        aggregate_path = warmer.aggregate_cache_path("openai", "codex")
        tampered = json.loads(aggregate_path.read_text(encoding="utf-8"))
        tampered["sha256"] = "0" * 64
        aggregate_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")

        calls = []

        def transport(request):
            calls.append(request.url)
            return self._github_transport(request)

        reader = GitHubHealthClient(
            self.cache_dir,
            token="super-secret",
            transport=transport,
            clock=lambda: "2026-08-01T10:00:00Z",
        )

        result = reader.repository_health("openai", "codex")

        self.assertEqual(expected, result)
        self.assertEqual(4, len(calls))

    def test_repository_health_rejects_tampered_aggregate_cache_without_token_or_secret_leak(self):
        # Break caught: invalid aggregate cache is trusted or leaks credentials while failing over to a live miss.
        warmer = GitHubHealthClient(
            self.cache_dir,
            token="super-secret",
            transport=self._github_transport,
            clock=lambda: "2026-07-31T10:00:00Z",
        )
        warmer.repository_health("openai", "codex")
        aggregate_path = warmer.aggregate_cache_path("openai", "codex")
        tampered = json.loads(aggregate_path.read_text(encoding="utf-8"))
        tampered["sha256"] = "0" * 64
        aggregate_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")

        client = GitHubHealthClient(self.cache_dir, token=None, transport=self._unexpected_transport)

        with self.assertRaisesRegex(ValueError, "GitHub token required for live request") as ctx:
            client.repository_health("openai", "codex")

        self.assertNotIn("super-secret", str(ctx.exception))

    @staticmethod
    def _unexpected_transport(_request):
        raise AssertionError("transport should not be called")

    @staticmethod
    def _github_transport(request):
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


if __name__ == "__main__":
    unittest.main()
