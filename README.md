# FemtoNews

飞秒 / 超快激光加工领域的社区周报网站。形式与代码框架沿用 [VibraNews](https://github.com/ForestBin-Raman/VibraNews)（ForestBin-Raman）：**每天自动抓取并发布新论文**，按周归为一期（每周一开新一期），编辑随时可以修改、删除、选特稿。

- 网站：纯静态页面（`index.html`），托管在 GitHub Pages，读取 `data/issues/*.json`
- 抓取：`scraper/femtonews_scraper.py`，数据源为 OpenAlex、Crossref、Europe PMC、arXiv（免费接口，不需要 API key）
- 自动化：GitHub Actions，每天新加坡时间 06:23 运行（`daily-update.yml`），抓过去 3 天的新论文，直接发布
- 第 1 期（2026-11-02 周）已预置：87 篇论文、13 篇 Feature Articles，摘要和 “Why it matters” 由编辑撰写

---

## 收录方向（分类体系）

网站侧栏 “Directions & Topics” 按五组分类，点 “中文” 可切换为中文名称。分类规则全部在 `scraper/config.yaml` 的 `categories`。

| 组 | 分类 |
|---|---|
| 研究方向 Directions | 硬脆材料加工 · 光波导与光子芯片 · 双光子聚合 · 光计算 · 光存储 · 表面微纳结构 / LIPSS · 光纤光栅与器件 · 选择性刻蚀与微流控 · 超快激光焊接 · 体内改性与纳米晶 · 微光学与超表面 · 激光诱导石墨烯 · 液相烧蚀与纳米颗粒 · 薄膜与二维材料 · 量子光子与色心 · 精密微加工与修调 |
| 方法与光场 Methods | 光束整形 / SLM（Bessel、全息多焦点）· 时空调控与脉冲串（SSTF、脉宽、GHz/MHz burst）· 超快光源与系统 · 过程诊断与泵浦探测 · 建模与仿真 · AI 与工艺优化 |
| 材料 Materials | 玻璃与熔融石英 · 蓝宝石与晶体 · SiC 与宽禁带 · 金刚石 · 硅与半导体 · 金属与合金 · 聚合物与光刻胶 · 钙钛矿与二维材料 · 陶瓷与涂层 · 生物组织 |
| 应用 Applications | 集成光子与通信 · 量子技术 · 半导体与封装 · 能源与电池 · 生物医学与生命科学 · 眼科与口腔 · 传感 · 热管理 · 航空航天与核能 · 成像与显示 |
| 其他 | 新闻与亮点 · 综述 · 招聘与招生 · 学位论文 |

每篇论文最多 5 个标签（方向 2、方法 1、材料 1、应用 1、其他 1，见 `category_limits`）。没有可用配图时，网站按第一个命中的方向画一个工艺示意小图（`glyphs`）。


## 网址与运行方式

- **网站**：https://linshulang12-u.github.io/FemtoNews/ ，GitHub Actions 每天新加坡时间 06:23 抓取并发布（GitHub 的定时任务常有几十分钟延迟）。
- **单文件版**：https://linshulang12-u.github.io/FemtoNews/FemtoNews.html 把全部数据嵌在一个 html 里，下载后双击即可离线浏览，也可以直接发给别人；缩略图从网站加载。

### Windows 电脑同步一份本地副本（不需要 Python）

双击 **`setup_windows.bat`**：下载最新的 `FemtoNews.html`，注册 Windows 计划任务 “FemtoNews daily sync”（每天 08:17 用系统自带的 curl 下载一次），然后打开网页。记录在 `logs\sync.log`。计划任务只在用户登录时运行。

### 不用 GitHub、在本机抓取（可选）

`setup_local_crawl.bat` 在本机安装 Python 依赖、注册 “FemtoNews daily update”（每天 06:23 运行 `run_daily.bat`：抓取 + 重建 `FemtoNews.html`），记录在 `logs\setup.log`、`logs\daily.log`。和 GitHub 方式二选一，否则两边的数据会各自更新。出问题时双击 `check_setup.bat`，结果写在 `logs\check.txt`。

## GitHub 部署：一次性设置（约 10 分钟）

1. **新建仓库**：在 GitHub 新建公开仓库，例如 `FemtoNews`，把本目录全部内容推上去（默认分支 `main`）。
2. **打开 Pages**：仓库 *Settings → Pages → Build and deployment → Source* 选 **GitHub Actions**。
3. **允许工作流写入和开 PR**：*Settings → Actions → General → Workflow permissions* 选 **Read and write permissions**，并勾选 **Allow GitHub Actions to create and approve pull requests**。
4. **填网址**：`scraper/config.yaml` 里的 `site.url`（已设为 `https://linshulang12-u.github.io/FemtoNews/`），只用于抓取时的 User-Agent。
5. **第一次发布**：推送到 `main` 会自动运行 *Deploy site to GitHub Pages*，几分钟后网站上线，显示第 1 期。
6. **手动试跑每日抓取**：*Actions → Daily update → Run workflow*。

## 日常流程

1. **每天早上 06:23（新加坡时间）**：自动抓取过去 3 天的新论文，加入当周这一期（以本周一的日期命名，如 `data/issues/2026-11-09.json`），直接发布。
   - 已经在任何一期出现过、或被你删除过的论文不会重复出现
   - 周一如果还没抓到新论文，网站继续显示上一期，不会出现空的一期
2. **随时修改**：在 GitHub 网页上打开当期的 `data/issues/<日期>.json`，点铅笔编辑，保存后网站自动更新：
   - 删掉不相关的文章，并把它的 `id` 加进 `"removed"`，以后不会再被抓回来
   - **Feature of the Week**：`"feature": true`，在 `"why"` 写一句为什么重要
   - **Feature Articles / Editor's Picks**：`"pick": true`
   - 改 `"summary"`、`"categories"`、`"institutions"`
3. 侧栏 Archive 保留所有往期。

**选稿助手**：`python scraper/curate.py status` 查看本期入选；把 `{"picks":[{"id":…,"why":…}], "feature":{"id":…}, "unpick":[…]}` 写成 JSON 后 `python scraper/curate.py apply <文件>`。每期 10–15 篇 Feature Articles，超过 15 篇时按入选日期替换最早的，Feature of the Week 不会被替换。也可以设一个每天的定时 Claude 任务来读当天新增论文、选稿、写推荐语。

**手动补抓**：*Actions → Manual run (draft PR) → Run workflow*，可补抓某段时间，或给某一期补缩略图（勾选 `refresh_figures`），结果以 PR 形式给你审核。

**投稿 / 手动加文章**：把 DOI 一行一个写进 `data/inbox.txt` 并保存，会**立即**触发一次抓取（不受关键词过滤），顺便补缩略图，处理完自动从 inbox 删除。

## 抓取范围与去杂

全部在 `scraper/config.yaml`：

- **收录**（`include` / `strong_include`）：标题命中即收录。专门工艺名（飞秒激光直写、laser-written waveguide、双光子聚合、LIPSS、选择性激光诱导刻蚀、5D 存储、隐形切割、GHz/MHz burst、时空聚焦等）在摘要里出现一次即收录；泛泛的 “femtosecond laser / ultrafast laser” 只在标题里算数（`title_only`），避免材料论文里一句 “用飞秒激光清洗” 就被收进来。
- **器件与量子实验**：摘要里出现一次 laser-written / laser-inscribed / ultrafast laser inscription / femtosecond laser micromachining / selective laser etching，或激光写入色心，即收录；量子类标签（玻色采样、量子行走、量子存储、离子阱 / Paul 阱芯片、NV 色心、纠缠光子等）优先显示。摘要里完全不提激光加工的量子论文抓不到，可以把 DOI 写进 inbox。
- **方法类必收**（`technique`）：出现超快激光工艺词且有方法学信号（“we develop/demonstrate … strategy / platform / printer …”，或加工动词 + 波导、光纤光栅、超表面、微透镜、存储、量子、蓝宝石、SiC、金刚石、玻璃等）的论文一律保留，强信号的直接上首页 Selected Papers。
- **排除**（`exclude`、`exclude_title`、`soft_exclude`）：LA-ICP-MS / LIBS 等分析用激光烧蚀、临床射频/静脉消融、阿秒与高次谐波、尾波加速等强场物理、双光子荧光成像、选区激光熔化 / 粉末床熔融与激光熔覆等宏观增材；超快磁学、瞬态吸收、锁模光纤激光、超连续谱等 “超快但不加工” 的论文，除非标题里有加工词。
- **常规临床应用**（`routine_application`）：飞秒激光辅助白内障 / LASIK / SMILE 的临床随访类论文不收；讲激光工艺本身的眼科论文照收。
- **核心期刊**（`core_journals`）：*Journal of Laser Micro/Nanoengineering* 每篇都收。
- **期刊质量**（`venues`）：主流出版社和 arXiv / bioRxiv 直接收；Research Square、Preprints.org、CyberLeninka、会议合集等排除；其他期刊 OpenAlex h-index ≥ 40 才收。
- 检索词：`openalex_terms`、`crossref_queries`、`europepmc_terms`、`arxiv_terms` / `arxiv_categories`。发现漏掉的方向，在这里加检索词并在 `categories` 里加规则。

| 数据源 | 覆盖 | 每日窗口 |
|---|---|---|
| OpenAlex | 几乎所有期刊，带摘要和作者机构（本领域主力） | 过去 30 天发表（重复自动跳过） |
| Crossref | 所有注册 DOI 的期刊（Optica、Elsevier、IOP、AIP …） | 过去 3 天注册的 DOI |
| Europe PMC | PubMed、PMC、bioRxiv 等（眼科、冷冻电镜等生物医学应用） | 过去 3 天入库 |
| arXiv | physics.optics、physics.app-ph、cond-mat.mtrl-sci、quant-ph 等 | 过去 3 天提交 |

## 缩略图规则

- **开放获取文章**：用文章页自带的预览图（通常是 Fig. 1 或图形摘要），图下注明许可。
- **非 OA 文章**：只用期刊封面，不用论文配图。
- **都没有**：网站画工艺示意图（切割、波导、2PP、光计算、存储、LIPSS、光纤光栅、焊接……）。

抓取遵守 `robots.txt`，每个站点请求间隔 1 秒。

## 本地运行

```
pip install -r scraper/requirements.txt pytest
python -m pytest -q scraper/tests                          # 离线自测（49 项）
python scraper/femtonews_scraper.py --daily                # 每日模式：过去 3 天的论文写入本周一期
python scraper/build_standalone.py                         # 重建可双击打开的 FemtoNews.html（--asset-base <网址> 让缩略图从网站加载）
python scraper/femtonews_scraper.py --issue-date 2026-11-09 # 按周模式
python -m http.server 8000                                 # 浏览 http://localhost:8000
```

常用参数：`--since/--until` 指定时间窗，`--no-figures` 跳过缩略图，`--dry-run` 只打印结果不写文件。

## 目录

```
index.html                 网站（一页，读取 data/）
data/issues/index.json     期次列表
data/issues/<日期>.json     每一期的文章
data/meetings.json         会议列表（手动维护）
data/inbox.txt             投稿 DOI
figs/  covers/             缩略图与期刊封面缓存（自动生成）
scraper/                   抓取脚本、配置、选稿助手、测试
.github/workflows/         每日抓取并发布、手动补抓/补图、推送后自动发布
```

## 致谢

页面布局、抓取与选稿流程改编自 ForestBin-Raman 的 [VibraNews](https://github.com/ForestBin-Raman/VibraNews)。公开发布前建议和原作者打个招呼，并保留这条致谢。
