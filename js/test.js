'use strict';
// 交叉校验：JS 实现的渲染结果必须与仓库里已提交的 docs/DISCLOSURE_MATRIX.md 逐字节一致。
//
// 那份文档由 tools/disclosure_matrix.py 生成并被 CI 的 `--check` 门锁住。所以这条断言
// 等价于「JS 与 Python 两份独立实现在同一份数据上给出同一个结果」。任何一边算错、
// 或者有人改了档案却没重算，这里都会失败。
//
// 运行: node js/test.js

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { compute, loadProfiles, render, wrap, resolveRoot, pyRound0 } = require('./disclosure');

let failed = 0;
function check(name, fn) {
  try { fn(); console.log(`✓ ${name}`); }
  catch (e) { failed += 1; console.log(`✗ ${name}\n    ${e.message.split('\n')[0]}`); }
}

const root = resolveRoot(null);
const profiles = loadProfiles(root);
const report = compute(profiles);

check('读到 19 份档案', () => {
  assert.strictEqual(report.n_products, 19, `got ${report.n_products}`);
});

check('全行业空白字段为 9 个', () => {
  assert.strictEqual(report.industry_blanks.length, 9,
    `got ${report.industry_blanks.length}: ${report.industry_blanks.join(', ')}`);
});

check('每 prompt 采样次数披露率为 0', () => {
  const row = report.groups
    .flatMap((g) => g.fields)
    .find((r) => r.field === 'measurement.samples_per_prompt');
  assert.ok(row, 'field missing');
  assert.strictEqual(row.disclosed, 0, `disclosed=${row.disclosed}`);
});

check('pyRound0 与 Python 的 round-half-even 一致', () => {
  assert.strictEqual(pyRound0(0.5), '0');
  assert.strictEqual(pyRound0(1.5), '2');
  assert.strictEqual(pyRound0(2.5), '2');
  assert.strictEqual(pyRound0(78.94736842105263), '79');
});

// 这条是核心：与 Python 的输出对齐
check('渲染结果与 docs/DISCLOSURE_MATRIX.md 逐字节一致', () => {
  const doc = path.join(root, 'docs', 'DISCLOSURE_MATRIX.md');
  if (!fs.existsSync(doc)) throw new Error(`missing ${doc} — 已发布的包不含 docs/，请在仓库检出目录运行`);
  const expected = fs.readFileSync(doc, 'utf-8');
  const actual = wrap(render(report));
  if (actual === expected) return;
  const a = actual.split('\n');
  const b = expected.split('\n');
  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    if (a[i] !== b[i]) {
      throw new Error(`第 ${i + 1} 行不一致\n    JS  : ${JSON.stringify(a[i])}\n    文档: ${JSON.stringify(b[i])}`);
    }
  }
  throw new Error('长度不一致');
});

console.log(failed ? `\n${failed} 项失败` : '\n全部通过：JS 与 Python 两份独立实现结果一致');
process.exitCode = failed ? 1 : 0;
