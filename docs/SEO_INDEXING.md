# 搜索引擎收录：做了什么、为什么、怎么复核

内部运维记录，不是报告的一部分（已在 `_config.yml` 的 `exclude` 里排除出站点构建）。

目的：让本仓库的内容能被搜索引擎发现。**最终目标是进入 AI 搜索的候选池**——
DeepSeek、豆包这类生成式引擎在回答时会检索网页，检索不到就完全没有机会。

---

## 起点：一个查了几天才发现的故障

`https://moreyiyi04-design.github.io/geo-monitor-audit/` **从上线起一直返回 404**。

原因：Pages 源配置为 `main` 分支 `/docs` 目录，但 `docs/` 下没有任何 index 文件。
Jekyll 构建成功（API 报 `status: built`），却生成不出首页。

**爬虫这几天来访拿到的全是 404 页——不是没被收录，是没有东西可收录。**

教训写在前面：

- **Pages 的 `status: built` 只说明构建没报错，不代表站点可访问。** 任何「已上线」
  的判断必须实际 `curl` 验证。
- 同期还发现 CI 从 07-31 起每次运行都是 failure（`tests/test_compiler.py` 里硬编码了
  一个本地临时目录的绝对路径，CI runner 上不存在），因为只看本地跑门通过就没查远端。
- 两次是同一类错误：**用间接信号代替直接验证**。

---

## 为什么必须靠 Pages 站，而不是 GitHub 仓库页

`github.com/robots.txt` 的实际情况：

```
禁止爬   */tree/  */blame/  */raw/  */archive/  /search$  /*q=
允许爬   /owner/repo      /*/blob/*
Sitemap  没有
```

**GitHub 不提供 sitemap，爬虫发现新仓库完全依赖外链。** 而新仓库外链为零。

更关键的是：`github.com` 不属于我们，**无法在 Google Search Console / Bing 站长工具
里验证所有权**，也就无法提交 sitemap 或请求编入索引。

`moreyiyi04-design.github.io` 这个 Pages 站是我们唯一能验证所有权、唯一能自己挂
sitemap 的表面。所以收录工作全部围绕它做。

---

## 做了什么

### 1. `docs/index.md` —— 修 404

站点首页。内容按「国内 GEO 监测工具清单 + 逐家免费档对比」组织，
而不是「披露率审计报告」。

**这个定位差异是实测出来的**，不是偏好：在候选池回放实验里
（`experiments/sim/` 于 scraper-python 仓库），同一个 URL、同一站点，
仅改标题与摘要的定位方式，被模型选中阅读的比例 **从 1/5 变为 5/5**。

### 2. `docs/_config.yml` —— sitemap 与站点元信息

```yaml
plugins:
  - jekyll-sitemap
```

`jekyll-sitemap` 在 GitHub Pages 的插件白名单内，无需自建构建流程。

同时把 `research/`、`superpowers/`、`DESIGN.md`、`METHODOLOGY.md`、本文件
排除出站点——它们是仓库内部文档，收进站点只会稀释主题相关性。

### 3. `docs/robots.txt` —— 显式放行并声明 sitemap

```
User-agent: *
Allow: /

Sitemap: https://moreyiyi04-design.github.io/geo-monitor-audit/sitemap.xml
```

### 4. Google Search Console 所有权验证

用 `jekyll-seo-tag` 的配置项，而不是改主题模板：

```yaml
google_site_verification: <GSC 给的 content 值>
```

`jekyll-seo-tag` 已随 `jekyll-theme-primer` 启用，改模板会多一处需要跟随主题
升级维护的地方。

### 5. IndexNow —— 唯一能脚本化的主动提交

Search Console 需要交互式登录，无法脚本化。**IndexNow 不需要任何账号**：
在站点上放一个 key 文件证明控制权，就能直接 POST 提交 URL。

参与方：Bing、Yandex、Seznam、Naver。**Google 不参与。**

```
docs/<key>.txt              key 文件，key 由仓库标识 sha256 派生而非随机数，便于复现
tools/submit_indexnow.py    提交脚本
```

key 文件必须与被提交 URL 同目录或更上层。本站在子路径 `/geo-monitor-audit/` 下，
所以 key 文件放在 `docs/` 并在请求里显式传 `keyLocation`。

脚本在提交前会自己拉一次 key 文件，校验可访问且内容匹配——否则要等 IndexNow
返回 422 才发现问题。

---

## 怎么复核（每一步都要实际访问，不看 API 状态）

```bash
# 站点四件套
for p in "" sitemap.xml robots.txt; do
  curl -s -o /dev/null -w "%{http_code} $p\n" \
    "https://moreyiyi04-design.github.io/geo-monitor-audit/$p"
done
# 期望：三个都是 200

# 验证标签真的在 <head> 里
curl -s https://moreyiyi04-design.github.io/geo-monitor-audit/ \
  | grep -o '<meta name="google-site-verification"[^>]*>'

# sitemap 里有哪些页面
curl -s https://moreyiyi04-design.github.io/geo-monitor-audit/sitemap.xml \
  | grep -o '<loc>[^<]*</loc>'

# 重新提交 IndexNow（内容更新后跑）
python3 tools/submit_indexnow.py            # --dry-run 只看不提交
# 期望：HTTP 200 或 202

# CI 是否真的通过（别只看本地）
gh run list --workflow verify.yml --limit 3 \
  --json conclusion,displayTitle --jq '.[]|"\(.conclusion)  \(.displayTitle)"'
```

---

## 已知的坑

**提交 sitemap 的时机。** 若在 sitemap 还是 404 时提交，GSC 会记为「无法抓取」
且**不会自动重试**——「上次读取时间」会一直是空的。修好文件后必须**删掉那条重新添加**。

**GSC 里填相对路径。** 资源前缀是 `https://moreyiyi04-design.github.io/geo-monitor-audit/`，
站点地图输入框只填 `sitemap.xml`。域名根 `https://moreyiyi04-design.github.io/` 是 404
（我们没有 root Pages 站），填绝对路径指到根会抓不到。

**Bing 不用重复验证。** GSC 验证通过后，Bing 站长工具里选「从 Google Search Console 导入」。

**改内容后要重跑 IndexNow。** 它是主动推送，不是轮询。

---

## 还没做的

- **npm 发布** —— 包已构建并在干净目录验证（`js/`），缺 npm token。
  发布后 npmjs 页面会形成一条指向仓库的外链。
- **外链** —— GitHub 无 sitemap，发现依赖外链。可能的来源：Awesome List 收录、
  包仓库页面（PyPI 已发、npm 待发）、第三方聚合站。
- **验证是否真的进了 AI 搜索的候选池** —— 这是真正的目标，收录只是前置条件。
  方法：用精确名 query 跑 `experiments/funnel_probe.py`，看仓库是否出现在
  `Found N web pages` 里。**在进池之前不要再改内容，改了也验证不了。**

---

## 时间预期

据公开实操经验，走完 Search Console 验证 + 提交 sitemap + 请求编入索引后，
Google 通常 3–7 天、Bing 5–10 天开始出现在结果里。IndexNow 提交后 Bing 侧可能更快。

**但收录 ≠ 进入 AI 搜索候选池。** 后者取决于检索引擎的索引和排序，
与 Google/Bing 是否同源目前未验证——已排除的是博查（18 次比较交集全 0）。
