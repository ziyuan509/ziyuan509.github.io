# Per-Website

个人学术主页。门户式结构（首页 + 五个子页），设计语言参照 al-folio：
整体零装饰，细节做足。纯静态输出，运行时零外部依赖。

**网站内容全部是英文**（`lang="en"`）。`data/*.toml` 里的注释是中文的，那是给你看的，
不会出现在页面上——写内容时所有字段值请用英文。

```bash
python build.py            # 生成到 docs/
python build.py --serve    # 生成后起 http://localhost:8000
```

`build.py` 每次跑完会列出「上线前还缺」的东西，照着补就行。

---

## 目录

```
build.py                生成器（全部模板逻辑都在这里）
tools/
  fetch_fonts.py        把 Google Fonts 抓到本地自托管
  make_og.py            生成 og:image 和 iOS 图标
data/
  site.toml             姓名、身份、简介、社交链接、首页 News、线上地址
  publications.toml     论文
  projects.toml         作品与工具
  cv.toml               在线简历
  games.toml            游戏手记
content/posts/*.md      文章（Markdown + 前置元数据）
assets/
  css/main.css          全部样式，顶部是设计 token
  css/fonts.css         自动生成，勿手改
  fonts/*.woff2         自托管字体
  js/site.js            主题切换、移动端菜单、复制 BibTeX
  img/                  图片放这里
docs/                   ← 构建产物，不要手改
```

改内容只动 `data/` 和 `content/`，改外观只动 `assets/css/main.css` 顶部的 token。

---

## 上线清单

### 1. 补内容（当前全是占位）

- [ ] `data/site.toml` — 姓名（我按 git config 猜的 `Ziyuan Qu`，多半不对）、身份、
      机构、邮箱、简介三段、社交链接
- [ ] `assets/img/profile.jpg` — 一张方形照片。没放的话首页显示姓名首字母，不会留空洞
- [ ] `data/publications.toml` — 真实论文。`authors` 里与 `site.name` 完全一致的会自动加粗
- [ ] `data/projects.toml` + **每个作品的配图**。Projects 页是 944×472 的大图布局，
      没有截图的话那一页就是一排大灰块，这是优先级最高的素材
- [ ] `data/cv.toml`、`data/games.toml`
- [ ] `content/posts/` — 删掉两篇示例
- [ ] `assets/cv.pdf` — 放进去后 CV 页的下载按钮会自动出现

### 2. 定域名，然后回填

域名一确定就把 `data/site.toml` 里的 `url` 填上（不带结尾斜杠），重新构建。
**留空的话 `canonical`、`og:url` 和 `sitemap.xml` 都不会生成**，Google 收录会受影响。

填完重跑一次 `python tools/make_og.py`，分享图底部会带上域名。

### 3. 推到 GitHub Pages

```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

仓库 **Settings → Pages → Deploy from a branch**，选 `main` 分支、`/docs` 目录。

- 仓库名叫 `<用户名>.github.io` → `base_url` 留空
- 仓库名是别的 → `base_url = "/<仓库名>"`，然后重新构建

**每次改完内容都要跑一次 `python build.py` 再提交**，`docs/` 是产物。

想换 Cloudflare Pages：连同一个仓库，构建命令留空，输出目录填 `docs`。因为产物已经
是静态文件，两边可以随时互换。

### 4. 绑自定义域名

在域名注册商的 DNS 面板加这些记录（`@` 表示根域名，有的面板要求填完整域名）：

| 类型 | 名称 | 值 |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |
| CNAME | `www` | `<你的用户名>.github.io` |

四条 A 记录要全加（GitHub 的四个入口），AAAA 是 IPv6，建议一起加。

然后 **Settings → Pages → Custom domain** 填域名保存，等 GitHub 检查通过后勾选
**Enforce HTTPS**（证书签发最多要等 24 小时，急不得）。

最后把域名填进 `data/site.toml` 的 `url`，重新构建。

> **重要**：`docs/CNAME` 由 `build.py` 根据 `url` 自动生成，**不要手动创建**。
> GitHub 在你绑定域名时会自己提交一个 `CNAME`，但 `build.py` 每次会清空 `docs/`，
> 手放的会被删掉、域名随即失效。填 `url` 才是唯一正确的做法。
> 填成 `*.github.io` 时不会生成（那是默认域名，写了反而出错）。

---

## 已经做好的上线项

| 项 | 说明 |
|---|---|
| favicon | `docs/favicon.svg`，姓名首字母配强调色，改名字会自动跟着变 |
| iOS 图标 | `assets/img/apple-touch-icon.png`，180×180 |
| 分享预览图 | `assets/img/og.png`，1200×630，含 Open Graph 与 Twitter Card 标签 |
| sitemap | 填了 `url` 后自动生成，含全部页面与文章 |
| robots.txt | 自动生成，填了 `url` 会带上 Sitemap 行 |
| 404 页 | `docs/404.html`，GitHub Pages 与 Cloudflare Pages 都会自动使用<br>（本地 `http.server` 不会，那是本地服务器的行为，不是 bug） |
| 字体自托管 | 见下 |

### 字体为什么要自托管

`fonts.googleapis.com` 在中国大陆基本不通。靠 CDN 引字体的话，大陆访客（包括你自己
不挂梯子的时候）看到的是系统默认字体，整套排版设计等于没有，还多一个渲染阻塞的失败请求。

现在字体文件在 `assets/fonts/`，**全站运行时零外部请求**，任何网络环境下表现一致。
六个文件合计约 138 KB。

换字体的流程：改 `tools/fetch_fonts.py` 里的 `FAMILIES` → 重跑 → 改 `main.css` 的
`--display` / `--sans`。

---

## 设计约束

改动前先读这几条，不然很容易把整体感破坏掉。

### 配色与字体

```css
--accent:  #6a3da8;   /* 唯一强调色：紫色，浅色下对比度 7.2:1 */
--display: "Schibsted Grotesk", ...;  /* 标题：紧、有性格的 grotesque */
--sans:    "Figtree", ...;            /* 正文：x-height 高，长文舒适 */
--mono:    "JetBrains Mono", ...;     /* 元信息、年份、pill */
```

标题和正文都是无衬线，靠**字重和字距**拉开层级（标题 600/700 + 负字距，正文 400 +
常规字距），不靠换字族的味道。深色模式强调色是 `#b79bf0`，对比度 8.2:1。

浅色定义在 `:root`，深色分别在 `@media (prefers-color-scheme: dark)` 和
`:root[data-theme="dark"]` 里覆盖同一批 token。**改配色只改 token，不要在组件规则里
写死颜色**，否则三种主题状态会对不上。

改 `--accent` 时记得同步 `build.py` 顶部的 `ACCENT` 常量（favicon 用），
以及 `tools/make_og.py` 里的 `ACCENT`（分享图用）。

### 一条硬规则：全站不用圆角

所有边框、图片、按钮、徽章一律直角，规整感靠直线和网格来立。
**加新组件时不要写 `border-radius`**——只要有一处圆角，整体那种规整感就散了。

### 悬浮动效：只用线和边

**不用阴影、不用位移、不用缩放。** 全站只有三个动效 token：

```css
--t:    140ms;                        /* 颜色一类的即时反馈 */
--t2:   240ms;                        /* 线条擦入这类有行程的 */
--ease: cubic-bezier(.2, .7, .3, 1);  /* 起步快、收尾稳 */
```

| 元素 | 效果 | 用的技术 |
|---|---|---|
| 卡片 / 大图 | 边缘一条 2px 强调线渐隐渐显 | `opacity` 过渡 |
| 导航项 | 同一条下划线，当前页常显 | 同上，hover 与 active 共用一条规则 |
| 正文链接 | 下划线加深并下沉一点 | `text-decoration-color` + `text-underline-offset` |
| 标题链接 | 下划线从透明淡入 | 同上，静止时线已占位所以不跳动 |
| pill / 社交方块 | 底色从下往上灌满 | `background-size` 走行程，不用伪元素 |

全站动画属性只允许这六个：`opacity`、`color`、`border-color`、`background-size`、
`text-decoration-color`、`text-underline-offset`。`--shadow` 只保留给移动端下拉菜单
那种功能性浮层。

**入场动效是另一类，不受上面「不用位移」的限制。** 带 `.reveal` 的块在滚动进入
视口时淡入 + 上移 10px，同屏多个错开 70ms。三条工程约束：

1. 隐藏行为写成 `.js .reveal`，`.js` 由 `<head>` 内联脚本添加——脚本没跑起来时
   内容照常显示，不会因为 JS 失效而永久看不见。
2. `prefers-reduced-motion: reduce` 时直接显示，不做任何过渡。
3. JS 里有 1.5 秒兜底定时器，无条件显示全部。IntersectionObserver 在后台标签页、
   被隐藏的容器里可能一直不触发，那种情况下内容消失的代价太大。

### 图片尺寸的层级

| 位置 | 比例 |
|---|---|
| 作品列表页卡片 | 16 / 10 裁切（网格要统一） |
| 作品详情页头图 | **保持原比例**，只限宽 |
| 作品详情页正文配图 | **保持原比例**，只限宽 |
| Publications 缩略图 | 4 / 3 裁切 |
| 游戏封面 | 3 / 4 裁切 |

**详情页的图不要裁。** 那些是带标注的技术图，统一裁成 16:9 会把标注和信息切掉。
只有列表页卡片需要统一比例，所以只裁那一张。

作品列表页是两列卡片，点进去是详情页 `projects/<slug>.html`。详情页内容写在
`projects.toml` 的 `lead`、`facts`、`[[project.section]]` 里；section 支持
`image`、`video`+`poster`、`code`+`code_lang` 三种媒体，`facts` 的图标从
`build.py` 的 `FACT_ICONS` 里选。

### 详情页的写作定位

讲**技术逻辑与交互实现**，不写制作流程。读者是 HCI 同行，他们关心「这个交互
为什么这样设计、系统怎么支撑它」，不关心先切了板材再装了投影仪。

### 视频而不是 GIF

UI 演示一律转成 MP4。三个原始 GIF 加起来 27 MB，直接放网页手机流量打不开；
转 H.264 后 2 MB，小一个数量级。`tools/make_project_images.py` 会调用
`imageio-ffmpeg` 自带的 ffmpeg 转换，并抽首帧做 poster。
视频是 `autoplay muted loop playsinline`，开了「减少动效」的用户由 `site.js`
改成手动播放。

---

## 数据字段

### 论文 `publications.toml`

| 字段 | 说明 |
|---|---|
| `authors` | 数组；等于 `site.name` 的会自动加粗 |
| `venue` / `venue_full` | 缩写显示在页面上，全称做悬停提示 |
| `year` | 整数，用来分组 |
| `award` | 可选，渲染成标题后的行内小徽章 |
| `selected` | `true` 的会出现在首页精选 |
| `thumb` | 可选；留空显示带首字母的占位块 |
| `links` | inline table，按书写顺序渲染成 pill 按钮 |
| `abstract` / `bibtex` | 可选；点 `abs` / `bib` 就地展开，BibTeX 带一键复制 |

`links` 的键名直接就是按钮上的字，随便加：

```toml
links = { pdf = "...", doi = "...", code = "...", video = "...", slides = "..." }
```

### 文章前置元数据

```markdown
---
title: 标题
date: 2026-07-14
excerpt: 列表页显示的一句话
tags: Method, Level design
---
```

Markdown 支持标题、列表、引用、代码块、链接、图片、粗体斜体、分隔线。
装了 `markdown` 包（`pip install markdown`）会自动改用它，语法支持更完整。

导航栏标签在 `build.py` 顶部的 `NAV` 里改。
