#!/usr/bin/env node
'use strict';
// npx geo-monitor-audit disclosure|verify|score
//
// 19 份证据化档案随包分发，装完无需克隆仓库即可运行。

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { compute, loadProfiles, render, resolveRoot } = require('./disclosure');

function usage() {
  console.log(`geo-monitor-audit — 19 家 GEO 监测厂商的逐字段披露率审计

  npx geo-monitor-audit disclosure [--json]   逐字段披露率矩阵
  npx geo-monitor-audit verify                校验证据快照的 sha256 与来源完整性
  npx geo-monitor-audit score                 列出各产品由字段重算得到的分数

  --repo <路径>   改为在指定的仓库检出目录上运行

数据与完整报告：https://github.com/moreyiyi04-design/geo-monitor-audit`);
}

function iterEnvelopes(node, prefix, out) {
  if (node === null || typeof node !== 'object' || Array.isArray(node)) return out;
  if ('conf' in node && 'v' in node) { out.push([prefix, node]); return out; }
  for (const [k, v] of Object.entries(node)) {
    iterEnvelopes(v, prefix ? `${prefix}.${k}` : k, out);
  }
  return out;
}

function cmdDisclosure(root, args) {
  const report = compute(loadProfiles(root));
  if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
  else console.log(render(report));
  return 0;
}

// 与 Python 侧 verify_evidence.py 检查同样的两件事：
// 每个非 unknown 字段必须挂来源；每条证据的 excerpt 文件 sha256 必须对得上。
function cmdVerify(root) {
  const profiles = loadProfiles(root);
  let failures = 0;
  for (const slug of Object.keys(profiles).sort()) {
    const profile = profiles[slug];
    const errors = [];
    const evidence = new Map();
    for (const rec of profile.evidence || []) evidence.set(rec.id, rec);

    for (const [dotted, env] of iterEnvelopes(profile, '', [])) {
      if (env.conf === 'unknown') continue;
      if (!Array.isArray(env.src) || env.src.length === 0) {
        errors.push(`${dotted}: non-unknown envelope requires at least one source`);
        continue;
      }
      for (const id of env.src) {
        if (!evidence.has(id)) errors.push(`${dotted}: unresolved evidence id ${id}`);
      }
    }

    for (const rec of profile.evidence || []) {
      if (!rec.excerpt_path || !rec.sha256) continue;
      const p = path.join(root, rec.excerpt_path);
      if (!fs.existsSync(p)) { errors.push(`evidence ${rec.id}: missing ${rec.excerpt_path}`); continue; }
      const got = crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
      if (got !== rec.sha256) errors.push(`evidence ${rec.id}: sha256 mismatch for ${rec.excerpt_path}`);
    }

    if (errors.length) {
      failures += 1;
      console.log(`✗ ${slug}`);
      for (const e of errors) console.log(`    ${e}`);
    } else {
      console.log(`✓ ${slug}  ${iterEnvelopes(profile, '', []).length} 个字段`);
    }
  }
  if (failures) { console.error(`\n${failures} 份档案未通过证据校验`); return 1; }
  console.log('\n全部通过：每个非 unknown 字段都挂着来源，每份快照的 sha256 一致');
  return 0;
}

function cmdScore(root) {
  const profiles = loadProfiles(root);
  for (const slug of Object.keys(profiles).sort()) {
    const s = profiles[slug].scores || {};
    const shown = Object.keys(s).sort().map((k) => `${k}=${s[k]}`).join(' ');
    console.log(`  ${slug}  ${shown || '(档案内无 scores)'}`);
  }
  console.log('\n分数由 Python 侧从字段重算（geo-monitor-audit score / tools/score.py --check）；');
  console.log('本命令只列出档案内已存的值，不重算——重算逻辑以 Python 实现为准。');
  return 0;
}

function main(argv) {
  const args = argv.slice(2);
  const cmd = args[0];
  if (!cmd || cmd === '-h' || cmd === '--help') { usage(); return 0; }
  const ri = args.indexOf('--repo');
  const explicit = ri >= 0 ? args[ri + 1] : null;
  let root;
  try { root = resolveRoot(explicit); } catch (e) { console.error(e.message); return 1; }

  switch (cmd) {
    case 'disclosure': return cmdDisclosure(root, args);
    case 'verify': return cmdVerify(root);
    case 'score': return cmdScore(root);
    default: console.error(`未知命令: ${cmd}\n`); usage(); return 1;
  }
}

process.exitCode = main(process.argv);
