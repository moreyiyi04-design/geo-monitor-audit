'use strict';
// 披露率矩阵的 JS 实现。
//
// 这不是对 Python 的封装——它独立读同一份 wiki/products/*.json 并自行渲染。
// 之所以要两份实现，是因为报告的核心断言（9 个字段全行业 0/19）值得被交叉验证：
// test.js 断言本文件的输出与仓库里已提交的 docs/DISCLOSURE_MATRIX.md 逐字节一致，
// 而那份文档由 tools/disclosure_matrix.py 生成。两边任何一边算错都会被发现。
//
// 字段分组、文案与数字格式必须与 tools/aris_geo/disclosure.py 保持同步。

const fs = require('fs');
const path = require('path');

const GROUPS = [
  ['measurement', '测量严谨性', [
    'measurement.capture_channel',
    'measurement.sampling_frequency',
    'measurement.samples_per_prompt',
    'measurement.sov_formula_public',
    'measurement.declares_noise_floor',
    'measurement.reports_confidence_interval',
    'measurement.model_version_pinning',
  ]],
  ['pricing', '价格透明', [
    'pricing.has_public_pricing',
    'pricing.trial',
    'pricing.entry_engines',
    'pricing.entry_prompts',
    'pricing.entry_seats',
    'pricing.min_commit',
    'pricing.annual_only',
    'pricing.refund_terms',
    'pricing.unit_inflation_risk',
  ]],
  ['exit', '退出与可迁移', [
    'exit.data_export',
    'exit.history_portable',
    'exit.contract_lock',
    'exit.content_hosted_by_vendor',
  ]],
  ['entity', '主体可核实', [
    'entity.registry_verifiable',
    'entity.team_public',
  ]],
  ['academic_anchor', '研究锚点', [
    'academic_anchor.peer_reviewed',
    'academic_anchor.reproducible_experiments',
    'academic_anchor.benchmark',
  ]],
];

const MARKER_START = '<!-- ARIS-GEO:DISCLOSURE:START -->';
const MARKER_END = '<!-- ARIS-GEO:DISCLOSURE:END -->';

// Python 的 f"{x:.0f}" 用 round-half-to-even，JS 的 toFixed 用 round-half-away-from-zero。
// 两者在 x.5 上不同，直接用 toFixed 会让交叉校验在边界值上假失败。
function pyRound0(x) {
  const floor = Math.floor(x);
  const frac = x - floor;
  if (Math.abs(frac - 0.5) > Number.EPSILON * 8) return String(Math.round(x));
  return String(floor % 2 === 0 ? floor : floor + 1);
}

function envelope(profile, dotted) {
  let node = profile;
  for (const key of dotted.split('.')) {
    if (node === null || typeof node !== 'object' || Array.isArray(node) || !(key in node)) return null;
    node = node[key];
  }
  const ok = node !== null && typeof node === 'object' && !Array.isArray(node) && 'conf' in node;
  return ok ? node : null;
}

function loadProfiles(repoRoot) {
  const dir = path.join(repoRoot, 'wiki', 'products');
  const files = fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort();
  const profiles = {};
  for (const f of files) {
    const payload = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8'));
    profiles[payload.slug || path.basename(f, '.json')] = payload;
  }
  if (!Object.keys(profiles).length) throw new Error(`no product dossiers under ${dir}`);
  return profiles;
}

function compute(profiles) {
  const slugs = Object.keys(profiles);
  const groups = [];
  for (const [key, label, fields] of GROUPS) {
    const rows = [];
    for (const dotted of fields) {
      let present = 0;
      let disclosed = 0;
      const disclosing = [];
      for (const slug of slugs) {
        const env = envelope(profiles[slug], dotted);
        if (env === null) continue;
        present += 1;
        if (env.conf !== 'unknown') { disclosed += 1; disclosing.push(slug); }
      }
      rows.push({
        field: dotted,
        leaf: dotted.split('.').pop(),
        present,
        disclosed,
        rate: present ? disclosed / present : 0.0,
        disclosing,
      });
    }
    groups.push({ key, label, fields: rows });
  }
  const industry_blanks = [];
  for (const g of groups) {
    for (const r of g.fields) if (r.present && r.disclosed === 0) industry_blanks.push(r.field);
  }
  return { n_products: slugs.length, groups, industry_blanks };
}

function render(report) {
  const total = report.n_products;
  const lines = [];
  lines.push('# 披露率矩阵：19 家 GEO 监测产品实际公开了什么');
  lines.push('');
  lines.push(
    `在 ${total} 份证据化产品档案上逐字段统计**公开材料能否确认该字段**。` +
    '「已披露」表示该字段在档案中挂有至少一个证据 id；「未披露」表示公开材料' +
    '不支持该字段，**不表示该能力不存在**。'
  );
  lines.push('');
  lines.push(
    '这张表由 `python3 tools/disclosure_matrix.py` 从 `wiki/products/*.json` 直接重算，' +
    '任何人可复现；证据快照带 SHA-256，篡改会被 `tools/verify_evidence.py --strict` 拒绝。'
  );
  lines.push('');

  if (report.industry_blanks.length) {
    lines.push('## 全行业空白');
    lines.push('');
    lines.push(`下列字段在 ${total} 份档案中**没有任何一家**能从公开材料确认：`);
    lines.push('');
    for (const field of report.industry_blanks) lines.push(`- \`${field}\``);
    lines.push('');
    lines.push(
      '这意味着采购方无法从公开材料判断这些产品的采样次数、误差、版本治理、' +
      '历史数据可迁移性与主体可核实性。**这些必须在 PoC 现场验收，不能靠官网。**'
    );
    lines.push('');
  }

  for (const group of report.groups) {
    lines.push(`## ${group.label}`);
    lines.push('');
    lines.push('| 字段 | 已披露 / 覆盖 | 披露率 |');
    lines.push('| --- | --- | --- |');
    for (const row of group.fields) {
      lines.push(`| \`${row.leaf}\` | ${row.disclosed} / ${row.present} | ${pyRound0(row.rate * 100)}% |`);
    }
    lines.push('');
  }

  lines.push('## 怎么用这张表');
  lines.push('');
  lines.push(
    '披露率低的字段不是「次要指标」，而是**供应商普遍回避的地方**——恰恰是 PoC 要重点验收的。' +
    '把披露率 0% 的字段直接抄进你的 PoC 验收清单，要求供应商现场给出答案并留证。'
  );
  lines.push('');
  return lines.join('\n');
}

function wrap(body) {
  return `${MARKER_START}\n${body.replace(/\s+$/, '')}\n${MARKER_END}\n`;
}

// 已发布的包把 wiki/ 放在 _bundled/ 下；源码检出时在仓库根。两处都找。
function resolveRoot(explicit) {
  const candidates = [];
  if (explicit) candidates.push(path.resolve(explicit));
  candidates.push(path.join(__dirname, '_bundled'));
  candidates.push(path.join(__dirname, '..'));
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, 'wiki', 'products'))) return c;
  }
  throw new Error('找不到 wiki/products/。请在仓库检出目录内运行，或用 --repo 指定路径。');
}

module.exports = { GROUPS, MARKER_START, MARKER_END, compute, loadProfiles, render, wrap, resolveRoot, pyRound0 };
