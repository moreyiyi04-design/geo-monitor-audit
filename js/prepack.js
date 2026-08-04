'use strict';
// 打包前把仓库根的 wiki/ 复制进 js/_bundled/，让已安装的包无需克隆仓库即可运行。
//
// npm 不能打包 package.json 所在目录之外的文件，所以必须复制而不能引用 ../wiki。
// _bundled/ 已在 .gitignore 中，不进版本库；每次 pack 前重新生成，避免陈旧副本。

const fs = require('fs');
const path = require('path');

const here = __dirname;
const repoRoot = path.join(here, '..');
const src = path.join(repoRoot, 'wiki');
const dst = path.join(here, '_bundled', 'wiki');

if (!fs.existsSync(path.join(src, 'products'))) {
  console.error(`prepack: 找不到 ${src}/products，无法打包`);
  process.exit(1);
}

fs.rmSync(path.join(here, '_bundled'), { recursive: true, force: true });
fs.cpSync(src, dst, { recursive: true });

// 同时带上渲染好的矩阵，让已安装的包也能跑 test.js 的一致性断言
const doc = path.join(repoRoot, 'docs', 'DISCLOSURE_MATRIX.md');
if (fs.existsSync(doc)) {
  const docDst = path.join(here, '_bundled', 'docs');
  fs.mkdirSync(docDst, { recursive: true });
  fs.copyFileSync(doc, path.join(docDst, 'DISCLOSURE_MATRIX.md'));
}

const n = fs.readdirSync(path.join(dst, 'products')).filter((f) => f.endsWith('.json')).length;
console.log(`prepack: 已打包 ${n} 份档案到 js/_bundled/wiki/`);
