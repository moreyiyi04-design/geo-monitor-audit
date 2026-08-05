#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Pages 站的 URL 提交给 IndexNow（Bing / Yandex / Seznam / Naver 共用）。

为什么用 IndexNow 而不是 Search Console：Search Console 需要登录 Google 账号完成
交互式验证，无法脚本化。IndexNow 不需要任何账号——只要在站点上放一个 key 文件证明
控制权，就能直接 POST 提交 URL。代价是 Google 不参与 IndexNow。

key 文件必须与被提交 URL 同目录或更上层。本站在子路径下（/geo-monitor-audit/），
所以 key 文件放在 docs/ 下并显式传 keyLocation。

用法:
    python3 tools/submit_indexnow.py            # 从 sitemap 读取全部 URL 并提交
    python3 tools/submit_indexnow.py --dry-run  # 只打印要提交什么
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "moreyiyi04-design.github.io"
BASE = f"https://{HOST}/geo-monitor-audit"
SITEMAP = f"{BASE}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
CTX = ssl.create_default_context()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def read_key() -> str:
    p = ROOT / "docs" / ".indexnow-key"
    if not p.is_file():
        raise SystemExit(f"缺少 {p}")
    return p.read_text(encoding="utf-8").strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=45, context=CTX).read().decode("utf-8", "ignore")


def sitemap_urls() -> list[str]:
    try:
        xml = fetch(SITEMAP)
    except Exception as exc:
        raise SystemExit(f"取 sitemap 失败：{exc}")
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    if not urls:
        raise SystemExit("sitemap 里没有 <loc>，先确认 Pages 已部署")
    return urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    key = read_key()
    key_location = f"{BASE}/{key}.txt"

    # 提交前先自证 key 文件可访问：IndexNow 会去拉这个文件，拉不到直接 422
    try:
        served = fetch(key_location).strip()
    except Exception as exc:
        raise SystemExit(f"key 文件不可访问 {key_location}：{exc}")
    if served != key:
        raise SystemExit(f"key 文件内容不匹配：期望 {key}，实际 {served[:40]}")

    urls = sitemap_urls()
    payload = {"host": HOST, "key": key, "keyLocation": key_location, "urlList": urls}

    print(f"host        {HOST}")
    print(f"keyLocation {key_location}  ✓ 可访问且内容匹配")
    print(f"提交 {len(urls)} 个 URL：")
    for u in urls:
        print(f"   {u}")
    if a.dry_run:
        return 0

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    try:
        resp = urllib.request.urlopen(req, timeout=60, context=CTX)
        print(f"\nIndexNow 返回 HTTP {resp.status}")
        # 200 已接收；202 已接收但 key 待验证。两者都算提交成功。
        return 0 if resp.status in (200, 202) else 1
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:300]
        print(f"\nIndexNow 返回 HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
