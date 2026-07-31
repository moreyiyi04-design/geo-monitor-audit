# Methodology

## Synthetic Fixture Warning

This repository currently publishes a **synthetic offline fixture** for the
`profound` slug. All committed excerpts use `https://example.invalid/...`
sources and explicitly identify themselves as synthetic test fixtures. The
fixture exists to exercise evidence validation, score recomputation, README
compilation, and CI gates offline. It does **not** represent live research,
vendor claims, or a product conclusion.

## Scope

ARIS-GEO studies GEO/AIO/AEO software artifacts rather than performing GEO for
its own brand. In this branch, the repository state is limited to one synthetic
fixture so the deterministic pipeline can be verified end-to-end without
credentials or network access.

## Known v1 Limitations

The current methodology inherits the six limitations required by DESIGN §9:

1. 维度集由海外标杆归纳,国内适配性未验证
2. `market: domestic | overseas` 的差异化必填字段集在 v1 只做了粗分
3. 「未披露」≠「没有」
4. 发现机制存在自指偏差: 用搜索发现 GEO 产品,天然更容易收录本来就擅长 GEO 的公司
5. 三个 persona 同模型,共享先验;补救依赖硬 checker 与公开 `unknowns[]` / `unresolved[]`
6. 无综合总分排名

## Ranking Policy

No total ranking is published. The repository only permits dimension-level
scores plus explicit labels because the system is designed to preserve
uncertainty instead of compressing it into one ordinal list.

## Label Sunset

标签必须能消失. Evidence carries `fetched_at`, and reruns are expected to update
compiled outputs when a product later discloses pricing, methods, or export
terms. Labels are observations tied to evidence dates, not permanent judgments.

## Copyright and Citation Posture

The committed `wiki/raw/` files store short synthetic excerpts only. Live
research mode is expected to store attributed excerpts rather than source-page
full text, and to keep all keys out of version control.
