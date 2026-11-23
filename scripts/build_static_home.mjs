#!/usr/bin/env node
/**
 * R1 全站 SSG：构建后生成静态首页（繁/简）+ 交互岛挂载点
 * - 输入：dist/index.html（Vite 产物，含 hashed asset 标签）
 * - 输出：dist/index.html（繁）、dist/cn/index.html（简）
 * - 静态首页包含完整 SEO 内容与全站内链；起卦 App 挂到 #app-root[data-island=1]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import HEXAGRAMS from '../src/data/hexagrams.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIST = path.join(ROOT, 'dist');
const SITE = JSON.parse(fs.readFileSync(path.join(ROOT, 'src/data/site_components.json'), 'utf8'));
const SITE_URL = SITE.site_url.replace(/\/$/, '');

const esc = (s = '') => String(s)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

function parsePosts(folder) {
  const dir = path.join(ROOT, folder);
  const out = [];
  for (const file of fs.readdirSync(dir).filter((f) => f.endsWith('.md'))) {
    const text = fs.readFileSync(path.join(dir, file), 'utf8');
    const m = text.match(/^---\n([\s\S]*?)\n---\n/);
    if (!m) continue;
    const meta = {};
    for (const line of m[1].split('\n')) {
      const i = line.indexOf(':');
      if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
    if (meta.slug && meta.title) out.push(meta);
  }
  return out.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
}

const copy = {
  tc: {
    lang: 'zh-Hant', prefix: '', switchHref: '/cn/', switchLabel: '简体中文',
    title: '決策之書 · 曾仕強易經商業決策助手',
    desc: '給海外華語中小微企業老闆的易經商業決策工具：輸入你正在糾結的生意難題，起一卦，看清處境、選項與下一步。',
    eyebrow: '曾仕強易經思想體系 · 商業決策',
    h1: '決策之書',
    tagline: '生意場上的抉擇，用《易經》看清一步。',
    lede: '給海外華語中小微企業老闆：合夥、用人、定價、轉型、收款——把眼前難題寫下來，起一卦，先把處境看清楚。',
    badges: ['免費', '免註冊', '30 秒出報告'],
    castTitle: '說說你現在最糾結的事',
    castDesc: '不用寫得漂亮，寫清楚就好：發生了什麼、你面前有哪幾條路、你最怕什麼。',
    whyTitle: '為什麼用《易經》看生意？',
    why: [
      ['看清處境', '卦不是水晶球，是一面鏡子。先把局面、關係、時機看清楚，再談怎麼走。'],
      ['看到兩面', '沒有一卦是純好純壞。每個選擇都有代價，也都有可以守住的东西。'],
      ['看到時間', '同一件事，早三個月和晚三個月，答案不一樣。卦提醒你現在處於哪一段。'],
    ],
    hexTitle: '六十四卦 · 商業決策解讀',
    hexDesc: '每一卦都對應一種生意處境。先看卦，再起卦。',
    blogTitle: '決策筆記',
    blogDesc: '易經入門、提問方法、真實生意難題的拆解。',
    allPosts: '查看全部文章 →',
    faqTitle: '常見問題',
    faq: [
      ['卦能預測未來嗎？', '不能。卦不是算盤，它不預測吉凶，只是把你自己看不清的處境翻給你看——答案，始終在你手上。'],
      ['可以對同一問題重複起卦嗎？', '不建議。卦反映的是當下處境；短時間反覆問同一件事，只會讓自己更亂。處境真的變了，再起一卦。'],
      ['報告能代替專業意見嗎？', '不能。醫療、法律、投資等專業問題，請諮詢持牌專業人士。本工具僅供決策思考參考。'],
      ['為什麼要選擇地區？', '營商環境、社會保障、人情壓力因地而異。報告會結合你所在地區，給出更貼近現實的建議。'],
    ],
    cta: '開始起卦 ↓',
    nav: ['提問', '易經', '筆記', '聯繫'],
    footer: ['關於本站', '隱私聲明', '免責聲明', '網站地圖'],
  },
  sc: {
    lang: 'zh-Hans', prefix: '/cn', switchHref: '/', switchLabel: '繁體中文',
    title: '决策之书 · 曾仕强易经商业决策助手',
    desc: '给海外华语中小微企业老板的易经商业决策工具：输入你正在纠结的生意难题，起一卦，看清处境、选项与下一步。',
    eyebrow: '曾仕强易经思想体系 · 商业决策',
    h1: '决策之书',
    tagline: '生意场上的抉择，用《易经》看清一步。',
    lede: '给海外华语中小微企业老板：合伙、用人、定价、转型、收款——把眼前难题写下来，起一卦，先把处境看清楚。',
    badges: ['免费', '免注册', '30 秒出报告'],
    castTitle: '说说你现在最纠结的事',
    castDesc: '不用写得漂亮，写清楚就好：发生了什么、你面前有哪几条路、你最怕什么。',
    whyTitle: '为什么用《易经》看生意？',
    why: [
      ['看清处境', '卦不是水晶球，是一面镜子。先把局面、关系、时机看清楚，再谈怎么走。'],
      ['看到两面', '没有一卦是纯好纯坏。每个选择都有代价，也都有可以守住的东西。'],
      ['看到时间', '同一件事，早三个月和晚三个月，答案不一样。卦提醒你现在处于哪一段。'],
    ],
    hexTitle: '六十四卦 · 商业决策解读',
    hexDesc: '每一卦都对应一种生意处境。先看卦，再起卦。',
    blogTitle: '决策笔记',
    blogDesc: '易经入门、提问方法、真实生意难题的拆解。',
    allPosts: '查看全部文章 →',
    faqTitle: '常见问题',
    faq: [
      ['卦能预测未来吗？', '不能。卦不是算盘，它不预测吉凶，只是把你自己看不清的处境翻给你看——答案，始终在你手上。'],
      ['可以对同一问题重复起卦吗？', '不建议。卦反映的是当下处境；短时间反复问同一件事，只会让自己更乱。处境真的变了，再起一卦。'],
      ['报告能代替专业意见吗？', '不能。医疗、法律、投资等专业问题，请咨询持牌专业人士。本工具仅供决策思考参考。'],
      ['为什么要选择地区？', '营商环境、社会保障、人情压力因地而异。报告会结合你所在地区，给出更贴近现实的建议。'],
    ],
    cta: '开始起卦 ↓',
    nav: ['提问', '易经', '笔记', '联系'],
    footer: ['关于本站', '隐私声明', '免责声明', '网站地图'],
  },
};

function postLinks(lang) {
  const prefix = lang === 'tc' ? '' : '/cn';
  const posts = parsePosts(lang === 'tc' ? 'blog_src' : 'blog_src_cn').slice(0, 6);
  return posts.map((p) => `
    <a class="post-card" href="${prefix}/blog/${esc(p.slug)}/">
      <span class="post-date">${esc(p.date || '')}</span>
      <span class="post-title">${esc(p.title)}</span>
      <span class="post-desc">${esc(p.description || '')}</span>
    </a>`).join('');
}

function hexLinks(lang) {
  const prefix = lang === 'tc' ? '' : '/cn';
  return [...HEXAGRAMS].sort((a, b) => Number(a.number) - Number(b.number)).map((h) => {
    const name = lang === 'tc' ? h.tc.name : h.sc.name;
    return `<a href="${prefix}/hexagram/${h.number}/"><span>第 ${Number(h.number)} 卦</span>${esc(name)}</a>`;
  }).join('');
}

function build(lang, assets) {
  const c = copy[lang];
  const canonical = lang === 'tc' ? `${SITE_URL}/` : `${SITE_URL}/cn/`;
  const alt = lang === 'tc' ? `${SITE_URL}/cn/` : `${SITE_URL}/`;
  const prefix = c.prefix;
  const faqLd = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: c.faq.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })),
  };
  const appLd = {
    '@context': 'https://schema.org', '@type': 'WebApplication',
    name: lang === 'tc' ? '決策之書' : '决策之书',
    description: c.desc, url: canonical, applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web', inLanguage: c.lang,
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD', description: lang === 'tc' ? '目前免費使用' : '目前免费使用' },
  };
  return `<!doctype html>
<html lang="${c.lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
${SITE.head_tags}
<title>${c.title}</title>
<meta name="google-site-verification" content="cFtiYTH3B3ZzC0Vk1tq-E1jBq3DwnbVM_B_ex3WuFRY">
<link rel="preconnect" href="https://api.dify.ai">
<link rel="preconnect" href="https://ko-fi.com">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-SGYWZGNCSH"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-SGYWZGNCSH');</script>
<meta name="description" content="${c.desc}">
<meta name="keywords" content="易經,決策,曾仕強,易經商業,商業決策,中小企業,創業,商業抉擇,易經,曾仕强,商业决策,企业经营,AI易经">
<meta name="robots" content="index, follow">
<link rel="canonical" href="${canonical}">
<link rel="alternate" hreflang="${c.lang}" href="${canonical}">
<link rel="alternate" hreflang="${lang === 'tc' ? 'zh-Hans' : 'zh-Hant'}" href="${alt}">
<link rel="alternate" hreflang="x-default" href="${SITE_URL}/">
<meta property="og:title" content="${c.title}">
<meta property="og:description" content="${c.desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="${canonical}">
<meta property="og:site_name" content="${lang === 'tc' ? '決策之書' : '决策之书'}">
<meta property="og:image" content="${SITE_URL}${SITE.og_image.path}">
<meta property="og:image:width" content="${SITE.og_image.width}">
<meta property="og:image:height" content="${SITE.og_image.height}">
<meta property="og:image:alt" content="決策之書 · 易經商業決策">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="${SITE_URL}${SITE.og_image.path}">
${assets.css}
<script type="application/ld+json">${JSON.stringify(appLd)}</script>
<script type="application/ld+json">${JSON.stringify(faqLd)}</script>
<style>
:root{--bg:#FAFAFA;--ink:#1A1A1A;--sub:#6B6B6B;--line:#E5E1D8;--gold:#8A6D3B;--gold2:#C8A96A;--card:#FFFFFF;--soft:#F6F1E7}
@media (prefers-color-scheme:dark){:root{--bg:#0F1115;--ink:#E8E6E0;--sub:#9A9DA6;--line:#2A2E3A;--gold:#C8A96A;--gold2:#D9BA7A;--card:#171A22;--soft:#1C2030}}
*{box-sizing:border-box}
html{color-scheme:light dark}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang TC","PingFang SC","Noto Sans TC","Noto Sans SC",sans-serif;line-height:1.85}
a{color:inherit}
.home-nav{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.home-nav-inner{max-width:1040px;margin:0 auto;padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:18px}
.home-brand{display:flex;align-items:center;gap:8px;text-decoration:none;font-weight:700;letter-spacing:.18em;white-space:nowrap}
.home-brand img{width:22px;height:22px}
.home-links{display:flex;align-items:center;gap:20px;font-size:13px;color:var(--sub)}
.home-links a{text-decoration:none;letter-spacing:.12em}
.home-links a:hover{color:var(--gold)}
.home-switch{border:1px solid var(--line);border-radius:7px;padding:4px 9px;font-size:12px}
.home-wrap{max-width:1040px;margin:0 auto;padding:0 20px 72px}
.hero{padding:64px 0 36px;text-align:center}
.hero .eyebrow{font-size:12px;letter-spacing:.28em;color:var(--gold);margin:0 0 14px}
.hero h1{font-size:clamp(40px,7vw,72px);line-height:1.15;letter-spacing:.1em;margin:0 0 14px}
.hero .tagline{font-size:clamp(17px,2.4vw,22px);margin:0 0 14px}
.hero .lede{max-width:720px;margin:0 auto;color:var(--sub);font-size:15px}
.badges{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin:20px 0 24px}
.badges span{font-size:12px;color:var(--gold);background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:5px 12px}
.btn{display:inline-block;background:var(--ink);color:var(--bg);text-decoration:none;padding:13px 30px;border-radius:999px;font-weight:700;letter-spacing:.08em}
.btn:hover{background:var(--gold)}
.cast{scroll-margin-top:70px;padding:10px 0 30px}
.cast h2,.sec h2{font-size:clamp(22px,3vw,30px);margin:0 0 8px}
.cast p,.sec p.sub{color:var(--sub);margin:0 0 18px}
.cast-box{max-width:640px;margin:0 auto;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:8px 18px 18px;box-shadow:0 6px 24px rgba(0,0,0,.05)}
.cast-box #app-root{min-height:340px}
.sec{padding:34px 0 6px}
.why-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}
.why-card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px}
.why-card h3{margin:0 0 6px;font-size:16px;color:var(--gold)}
.why-card p{margin:0;color:var(--sub);font-size:14px}
.hex-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:18px}
.hex-grid a{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 10px;font-size:13px;line-height:1.5}
.hex-grid a span{display:block;color:var(--sub);font-size:11px;letter-spacing:.12em}
.hex-grid a:hover{border-color:var(--gold2);color:var(--gold)}
.all-link{display:inline-block;margin-top:14px;color:var(--gold);font-size:13px;text-decoration:none}
.posts-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:18px}
.post-card{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.post-card:hover{border-color:var(--gold2)}
.post-date{display:block;font-size:11px;color:var(--sub);letter-spacing:.1em;margin-bottom:4px}
.post-title{display:block;font-size:14px;font-weight:700;margin-bottom:4px}
.post-desc{display:block;font-size:12.5px;color:var(--sub);line-height:1.65}
.faq-list{margin-top:16px;display:grid;gap:8px}
.faq-list details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px}
.faq-list summary{cursor:pointer;font-weight:700;font-size:14px}
.faq-list p{color:var(--sub);font-size:13px;margin:8px 0 0}
.home-footer{margin-top:44px;border-top:1px solid var(--line);padding-top:18px;text-align:center;color:var(--sub);font-size:12.5px}
.home-footer a{text-decoration:none;margin:0 6px}
.home-footer a:hover{color:var(--gold)}
@media (max-width:760px){.home-links{gap:11px}.home-links a:nth-child(4){display:none}.why-grid{grid-template-columns:1fr}.hex-grid{grid-template-columns:repeat(2,1fr)}.posts-grid{grid-template-columns:1fr}.hero{padding-top:44px}}
</style>
</head>
<body>
<nav class="home-nav" aria-label="${lang === 'tc' ? '主導覽' : '主导航'}">
  <div class="home-nav-inner">
    <a class="home-brand" href="${prefix}/"><img src="/mark-header.png" alt="" width="22" height="22">${lang === 'tc' ? '決策之書' : '决策之书'}</a>
    <div class="home-links">
      <a href="#cast">${c.nav[0]}</a>
      <a href="${prefix}/hexagram/">${c.nav[1]}</a>
      <a href="${prefix}/blog/">${c.nav[2]}</a>
      <a href="${prefix}/contact/">${c.nav[3]}</a>
      <a class="home-switch" href="${c.switchHref}">${c.switchLabel}</a>
    </div>
  </div>
</nav>
<div class="home-wrap">
  <header class="hero">
    <p class="eyebrow">${c.eyebrow}</p>
    <h1>${c.h1}</h1>
    <p class="tagline">${c.tagline}</p>
    <p class="lede">${c.lede}</p>
    <div class="badges">${c.badges.map((x) => `<span>${x}</span>`).join('')}</div>
    <a class="btn" href="#cast">${c.cta}</a>
  </header>

  <section class="cast" id="cast">
    <h2>${c.castTitle}</h2>
    <p>${c.castDesc}</p>
    <div class="cast-box"><div id="app-root" data-island="1"></div></div>
  </section>

  <section class="sec">
    <h2>${c.whyTitle}</h2>
    <div class="why-grid">${c.why.map(([h, p]) => `<div class="why-card"><h3>${h}</h3><p>${p}</p></div>`).join('')}</div>
  </section>

  <section class="sec">
    <h2>${c.hexTitle}</h2>
    <p class="sub">${c.hexDesc}</p>
    <div class="hex-grid">${hexLinks(lang)}</div>
    <a class="all-link" href="${prefix}/hexagram/">${lang === 'tc' ? '查看六十四卦索引 →' : '查看六十四卦索引 →'}</a>
  </section>

  <section class="sec">
    <h2>${c.blogTitle}</h2>
    <p class="sub">${c.blogDesc}</p>
    <div class="posts-grid">${postLinks(lang)}</div>
    <a class="all-link" href="${prefix}/blog/">${c.allPosts}</a>
  </section>

  <section class="sec">
    <h2>${c.faqTitle}</h2>
    <div class="faq-list">${c.faq.map(([q, a]) => `<details><summary>${q}</summary><p>${a}</p></details>`).join('')}</div>
  </section>

  <footer class="home-footer">
    <div>
      <a href="${prefix}/about/">${c.footer[0]}</a> ·
      <a href="${prefix}/privacy/">${c.footer[1]}</a> ·
      <a href="${prefix}/disclaimer/">${c.footer[2]}</a> ·
      <a href="${prefix}/sitemap/">${c.footer[3]}</a>
    </div>
    <p>${lang === 'tc' ? '曾仕強教授易經思想體系' : '曾仕强教授易经思想体系'}</p>
  </footer>
</div>
${assets.scripts}
</body>
</html>`;
}

const built = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8');
const assets = {
  css: [...built.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*>/g)].map((m) => m[0]).join('\n'),
  scripts: [...built.matchAll(/<script\b[^>]*type="module"[^>]*><\/script>/g)].map((m) => m[0]).join('\n'),
};
if (!assets.scripts) throw new Error('未找到 Vite module script，无法生成静态首页');

fs.writeFileSync(path.join(DIST, 'index.html'), build('tc', assets), 'utf8');
fs.mkdirSync(path.join(DIST, 'cn'), { recursive: true });
fs.writeFileSync(path.join(DIST, 'cn/index.html'), build('sc', assets), 'utf8');
console.log('✓ 静态首页已生成：dist/index.html（繁）、dist/cn/index.html（简）');
