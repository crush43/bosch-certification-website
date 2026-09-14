# 认证网站：Excel → JSON → 页面字段映射

> STEP 1 分析产物。本文只记录现状、映射和待确认问题；本步骤未修改 `index.html`，也未实现同步程序。

> STEP 3 最新源文件复核：业务方已从最新版 ENTER1 Excel 删除 L5 的重复图片对象。最新版实际检测为 32 个 ENTER1 图片对象，L5 只有 1 张。下方 3.4 中的 33 项明细保留为 STEP 1 历史取证，不得再作为当前数量断言；同步程序按每次 Excel 实际内容动态计算。

## 1. 已核对的输入

| 文件 | 作用 | 核对结果 |
|---|---|---|
| `index.html` | 当前网站原型 | 单文件 SPA；业务数据硬编码为 `D1`、`D2`、`D3` |
| `附件/ENTER 1-Basic Information.xlsx` | ENTER1 数据源 | 3 个 Sheet；`铭牌信息` 有效，范围 `A2:S7`，实际数据行 3–6 |
| `附件/ENTER 2-Certification Mark.xlsx` | ENTER2 数据源 | Sheet `Certification Mark`，范围 `A1:F8`，数据行 2–8 |
| `附件/ENTER 3-Reference Link.xlsx` | ENTER3 数据源 | Sheet `Reference Link`，范围 `A1:B5`，有效数据行 1、3、5 |
| `设计要求.txt` | 初始需求 | 三级筛选、Corded/Cordless、完整铭牌及分区信息 |
| `附件/新要求.txt` | 三模块需求 | HOME + ENTER1/2/3、跨模块导航、统一备注 |

补充核对了 `开发指导文档.md`、`CLAUDE.md`、现有 `img_new_hd/` 和图片处理脚本，以确认当前字段含义及既有图片来源。

## 2. 当前页面数据入口

当前 `index.html` 中：

- `D1`：4 条基础信息记录；`renderE1()`、`initE1Filters()`、`getE1Filtered()` 消费。
- `D2`：7 条认证标志记录；`initE2Filters()`、`renderE2()` 消费。
- `D3`：3 条参考链接；`renderE3()` 消费。
- `P = 'img_new_hd/'`：当前硬编码图片路径前缀。
- `L(obj)`：按当前语言取业务文本，回退顺序为当前语言 → `zh` → `en` → 空字符串。

目标链路为：

```text
Excel
  → scripts/sync_excel.py
  → data/*.json + assets/generated/**/*
  → index.html fetch()
  → 复用现有 renderE1 / renderE2 / renderE3
```

## 3. ENTER1 映射

### 3.1 Sheet 与记录粒度

- 文件：`附件/ENTER 1-Basic Information.xlsx`
- 主 Sheet：`铭牌信息`
- 表头行：第 2 行
- 数据行：第 3–6 行
- 一行代表一个 `国家 × 产品类别 × 产品名称 × Corded/Cordless` 铭牌要求。
- `包装标签`、`说明书` 两个 Sheet 当前为空；本阶段不生成对应业务记录，但同步器应保留未来扩展入口。

### 3.2 列映射

| Excel 列 | Header | 建议 JSON 字段 | 当前 `D1` 字段 | 当前页面消费位置 | 类型/清洗规则 |
|---|---|---|---|---|---|
| A | 国家 | `country` | `country` | 筛选、卡片副标题 | `{zh,en,de}`；本阶段只写 `zh` |
| B | 产品类别 | `category` | `category` | 级联筛选、卡片副标题 | `{zh,en,de}`；本阶段只写 `zh` |
| C | 产品名称 | `product` | `product` | 级联筛选、卡片标题 | `{zh,en,de}`；本阶段只写 `zh` |
| D | Corded/Cordless | `powerType` | `corded` | `getE1Filtered()`、卡片副标题 | `Corded`、`Cordless` 或空 |
| E | 示例 | `example` | `example` | 完整铭牌、字段 1 图片 | 图片字段；见 3.4 的数组冲突 |
| F | 型号 | `model` | `model` | 顶部徽标、字段 1 | 文本；`/` → `""` |
| G | 裸机号 | `bareModel` | `bareModel` | 字段 1 | 文本；作为标识符读取，不能转数字 |
| H | 参数 | `specs` | `specs` | 字段 2 | 文本；需保留特殊符号及富文本拼接结果 |
| I | 生产年月 | `dateCode` | `dateCode` | 字段 3 | 文本；不能解析成日期 |
| J | 认证标志 | `cert` | `cert` | 字段 4 | 图片数组；`/` → `[]` |
| K | 环保标志 | `eco` | `eco` | 字段 5 | 图片数组；同一单元格可多图 |
| L | 原产地信息 | `origin` | `origin` | 字段 6 | 图片数组 |
| M | Class II 标志 | `class2` | `class2` | 字段 7 | 图片数组；`/` → `[]` |
| N | 制造商/生产者信息 | `manufacturer` | `mfr` | 字段 8 | 图片数组；页面字段名需最小适配 |
| O | WEEE标志 | `weee` | `weee` | 字段 9 | 图片数组 |
| P | 阅读说明书 | `manual` | `manual` | 字段 10 | 图片数组 |
| Q | IP等级 | `ip` | `ip` | 字段 11 | 文本；`/` → `""` |
| R | 防护标志 | `protect` | `protect` | 字段 12 | 图片数组；`/` → `[]` |
| S | 其他特殊标签 | `other` | `other` | 字段 13 | 图片数组；`/` → `[]` |

额外生成字段：

| JSON 字段 | 来源/规则 |
|---|---|
| `id` | 对 `country + category + product + powerType + model` 做规范化后生成 deterministic ID；不能单独使用行号 |

### 3.3 当前四条记录基准

| Excel 行 | 国家 | 类别 | 产品 | 电源 | 型号 |
|---:|---|---|---|---|---|
| 3 | 中国 | 电动工具 | 电锤 | Corded | GBH6-42VB |
| 4 | 欧盟 | 电动工具 | 角磨 | Cordless | GWS 18V-15 S |
| 5 | 欧盟 | 家用电器 | 吸尘器 | Corded | GAS 12-25 PL |
| 6 | 乌克兰 | 电动工具 | 台锯 | Corded | GTS 635-216 |

### 3.4 ENTER1 图片锚点

图片归类必须使用 `anchor 起始行/列 → 第 2 行 Header`，不能依赖 Excel 内部图片名或媒体文件名。OOXML 中行列均为 0-based，转成业务坐标时必须各加 1。

| 序号 | 锚点 | Header/JSON 字段 | Excel 对象名 | OOXML 媒体 |
|---:|---|---|---|---|
| 1 | E3 | 示例 / `example` | Picture 1 | `image1.png` |
| 2 | M3 | Class II / `class2` | Picture 2 | `image2.png` |
| 3 | J3 | 认证标志 / `cert` | Picture 3 | `image3.png` |
| 4 | N3 | 制造商 / `manufacturer` | Picture 4 | `image4.png` |
| 5 | L3 | 原产地 / `origin` | Picture 6 | `image5.png` |
| 6 | K3 | 环保标志 / `eco` | 图片 12 | `image6.png` |
| 7 | K3 | 环保标志 / `eco` | 图片 13 | `image7.png` |
| 8 | E4 | 示例 / `example` | Picture 5 | `image8.png` |
| 9 | J4 | 认证标志 / `cert` | Picture 10 | `image9.png` |
| 10 | L4 | 原产地 / `origin` | Picture 11 | `image10.png` |
| 11 | N4 | 制造商 / `manufacturer` | Picture 12 | `image4.png` |
| 12 | O3 | WEEE / `weee` | Picture 13 | `image11.png` |
| 13 | O4 | WEEE / `weee` | Picture 14 | `image11.png` |
| 14 | R4 | 防护标志 / `protect` | Picture 16 | `image12.png` |
| 15 | S4 | 其他标签 / `other` | Picture 18 | `image13.png` |
| 16 | E5 | 示例 / `example` | Picture 19 | `image14.png` |
| 17 | J5 | 认证标志 / `cert` | Picture 20 | `image9.png` |
| 18 | L5 | 原产地 / `origin` | Picture 21 | `image10.png` |
| 19 | N5 | 制造商 / `manufacturer` | Picture 22 | `image4.png` |
| 20 | O5 | WEEE / `weee` | Picture 23 | `image11.png` |
| 21 | P5 | 阅读说明书 / `manual` | Picture 24 | `image15.png` |
| 22 | E6 | 示例 / `example` | Picture 25 | `image16.png` |
| 23 | P6 | 阅读说明书 / `manual` | Picture 26 | `image17.png` |
| 24 | P3 | 阅读说明书 / `manual` | Picture 27 | `image17.png` |
| 25 | P4 | 阅读说明书 / `manual` | Picture 28 | `image17.png` |
| 26 | L5 | 原产地 / `origin` | Picture 30 | `image10.png` |
| 27 | L6 | 原产地 / `origin` | Picture 31 | `image10.png` |
| 28 | N6 | 制造商 / `manufacturer` | Picture 32 | `image4.png` |
| 29 | O6 | WEEE / `weee` | Picture 33 | `image11.png` |
| 30 | M6 | Class II / `class2` | Picture 34 | `image2.png` |
| 31 | R6 | 防护标志 / `protect` | Picture 35 | `image18.png` |
| 32 | S6 | 其他标签 / `other` | Picture 36 | `image19.png` |
| 33 | J6 | 认证标志 / `cert` | Picture 37 | `image20.png` |

核对结论：

- Excel 有 **33 个图片对象**，但只有 **20 份独立媒体二进制**；多行复用相同媒体是正常情况。
- `K3` 有两张不同图片，应生成 `eco[0]`、`eco[1]`。
- `L5` 有两个完全相同的锚点，且都指向 `image10.png`。这是重复图片对象，不是两张不同图片。
- 当前 `img_new_hd/` 导出了 33 个 ENTER1 文件，包括重复的 `e1_eu_vacuum_origin_26.png`；当前 `D1` 没有引用该重复文件。
- 因此按“图片对象数”统计为 33，按“去除同单元格同内容重复后的逻辑图片数”统计为 32。

## 4. ENTER2 映射

### 4.1 Sheet 与列映射

- 文件：`附件/ENTER 2-Certification Mark.xlsx`
- Sheet：`Certification Mark`
- 表头行：第 1 行
- 数据行：第 2–8 行

| Excel 列 | Header | 建议 JSON 字段 | 当前 `D2` 字段 | 当前页面消费位置 | 规则 |
|---|---|---|---|---|---|
| A | 国家 | `country` | `country` | 国家筛选、卡片地区、搜索 | `{zh,en,de}`；本阶段只写 `zh` |
| B | 标志 | `name` | `name` | 卡片标题、搜索 | 必填文本 |
| C | 图纸编号 | `drawing` | `drawing` | 展开状态 key、显示、搜索 | 建议必填；读取富文本全部 runs 后 trim |
| D | 标志示意图 | `image` | `img` | 卡片图标 | Excel 内嵌图片；页面字段名需最小适配 |
| E | 关键备注 | `notes` | `notes` | 展开详情、搜索 | `{zh,en,de}`；保留换行 |
| F | 适用产品 | `products` | `products` | 产品筛选、标签、搜索 | `{zh,en,de}`；保留源文本 |

额外生成字段：

| JSON 字段 | 来源/规则 |
|---|---|
| `id` | 优先使用规范化图纸编号，如 `e2_161111b021`；若图纸编号为空，使用名称与国家的 hash fallback |

当前 `D2.nameCn` 是 HTML 中人工补充的三语全称，Excel 没有该列，目标 JSON 示例也不包含它。同步后搜索逻辑必须允许 `nameCn` 缺失，不能要求同步器编造翻译。

### 4.2 ENTER2 图片锚点

| Excel 行 | 锚点 | 标志 | 图纸编号（trim 后） | OOXML 媒体 |
|---:|---|---|---|---|
| 2 | D2 | CE | `161111B021` | `image1.png` |
| 3 | D3 | CCC | `161111B002` | `image2.png` |
| 4 | D4 | China RoHS II for compliance | `161111B015` | `image3.png` |
| 5 | D5 | China RoHS II for noncompliance | `161111B02F` | `image4.png` |
| 6 | D6 | UL | `161111B006` | `image5.png` |
| 7 | D7 | ETL | `161111B014` | `image6.png` |
| 8 | D8 | CSA | `161111B016` | `image7.png` |

ENTER2 为 7 个图片对象、7 份独立媒体，无重复锚点。

## 5. ENTER3 映射

### 5.1 实际工作簿形态

- 文件：`附件/ENTER 3-Reference Link.xlsx`
- Sheet：`Reference Link`
- 工作簿当前**没有表头行**。
- 第 1、3、5 行直接是数据；第 2、4 行为空。

| Excel 列 | 业务含义 | 建议 JSON 字段 | 当前 `D3` 字段 | 规则 |
|---|---|---|---|---|
| A | 名称 | `title` | 当前无；由 `key` 对应 i18n 文案 | 必填；完全空行忽略 |
| B | URL | `url` | `url` | 必填；仅接受 `http://` 或 `https://` |
| — | 稳定标识 | `id` | 当前无 | `title + URL` 规范化后生成 deterministic ID |
| — | 页面兼容键 | `key` | `key` | 可从已知名称映射；不能成为新增链接的显示前提 |

当前三条基准数据：

| Excel 行 | 名称 | 当前 `D3.key` |
|---:|---|---|
| 1 | PT/ECS | `PT` |
| 3 | News | `News` |
| 5 | EUDoC | `EUDoC` |

当前 `renderE3()` 不读取 Excel 标题，而是用 `key` 拼接 `lkPT`、`lkNews` 等 i18n key。若 Excel 新增任意名称，页面会找不到对应标题/描述翻译。因此 STEP 4 必须让页面优先显示 JSON `title`，现有已知 key 仍可保留 UI 描述和图标作为增强。

## 6. 清洗、校验与读取约束

### 6.1 通用清洗

- 字符串去除首尾空白；内部换行保留。
- Excel 值 `/`：文本字段转 `""`，图片字段转 `[]`。
- 完全空白行忽略；部分必填字段为空时不能静默忽略，必须报告文件、Sheet、行号、字段和原因。
- 标识符（裸机号、图纸编号）始终按文本读取，不能数值化。
- 不自动翻译；`en`、`de` 无来源时为空，由页面 `L()` 回退中文。

### 6.2 富文本/共享字符串

- ENTER1 `H4` 参数实际由 Excel 富文本/共享字符串存储，完整拼接结果为 `18V n0=3400-11000 min-1 ø125mm M14`。
- ENTER2 `C2:C8` 图纸编号也以共享字符串形式保存，末尾存在空格；必须拼接所有 text runs 并 trim。
- 同步器不能只取第一个 `<t>` 节点，也不能把 rich-text 对象直接序列化。

### 6.3 图片关系读取

图片链路为：

```text
worksheet.xml
  → worksheet rels
  → drawing*.xml 中 oneCellAnchor/twoCellAnchor
  → drawing rels 中 r:embed
  → xl/media/image*.*
```

实现时应同时记录：Sheet、起始 row、起始 col、header、媒体关系和内容 hash。openpyxl 可作为主要读取接口，但必须用 OOXML drawing/media 关系补足并验证锚点，特别是重复/复用图片。

## 7. 与当前 HTML 的最小兼容改造点（STEP 4 才执行）

| 目标 JSON | 当前 HTML 假设 | 最小改造 |
|---|---|---|
| `powerType` | 使用 `item.corded` | 筛选及卡片改读 `powerType`，或加载后做一次兼容归一化 |
| `manufacturer` | 使用 `item.mfr` | 字段 8 改读 `manufacturer` |
| ENTER2 `image` | 使用 `m.img` | 卡片改读 `m.image` |
| 图片字段统一数组 | `imgBox()` 已支持数组/字符串，但完整 `example` 只支持字符串 | 明确 schema 后让完整铭牌选择 `example[0]`，字段块展示全部图片 |
| 缺少 `nameCn` | 搜索 blob 直接调用 `L(m.nameCn)` | 允许字段缺失，搜索以 Excel 字段为准 |
| ENTER3 `title` | 标题仅来自 `t('lk'+key)` | 优先读 JSON `title`，已知 key 再补充描述/图标 |
| 异步 fetch | 页面末尾立即 `applyLang(); go('home')` | 增加 loading/error 状态，数据成功后再初始化依赖数据的视图 |

本阶段不需要改变 CSS、导航结构、三语言 UI 文案或现有渲染布局。

## 8. 需要特别处理或确认的问题

1. **历史重复图片已由业务方修正**：最新版 L5 只有 1 张图片；数量必须动态计算。同步器仍保留通用的“同 Sheet + 同 anchor + 同内容 hash”去重与 Warning 机制。
2. **`example` 类型已确认**：ENTER1 所有图片字段统一为数组，页面以第一张作为完整铭牌主图。
3. **ENTER3 无表头**：当前文件不能按普通“首行为 Header”读取。推荐 STEP 3 兼容当前无表头结构，同时允许未来使用明确的 `名称 | URL` 表头。
4. **字段名不完全一致**：目标 schema 的 `powerType`、`manufacturer`、`image` 与当前 HTML 的 `corded`、`mfr`、`img` 不一致，需要在 STEP 4 做极小适配，不能只替换数组来源。
5. **ENTER2 人工翻译字段**：`nameCn` 没有 Excel 来源；不得继续把它当必需数据。
6. **多图与重复图必须区分**：`K3` 是合法多图，`L5` 是重复对象。不能简单按“同一单元格只取一张”或“所有 anchor 全收”处理。
7. **现有脚本不可复用为正式同步器**：`process_new_images.py` 写死 `C:\Users\Joe\Desktop\2`，依赖已不存在的 `img_new/`；`sharpen_v2.py` 依赖已不存在的 `img/`。新同步器必须基于项目根目录解析路径。
8. **当前机器的 `python` 命令是 Windows Store 占位程序**：STEP 3 开发/验收前需要可用的 Python 3 环境，并安装 requirements。
9. **本地直接双击 HTML 时 fetch 可能被浏览器拦截**：JSON 版必须通过本地 HTTP 服务预览，例如 `python -m http.server 8080`，README 需明确说明。
10. **generated 清理边界**：同步只能完整重建 `assets/generated/enter1/` 与 `assets/generated/enter2/`，不能触碰 `logo.png`、`img_new_hd/` 或其他人工资源。

## 9. STEP 2/3 计划创建或修改的文件

### STEP 2：只设计 schema

- 新建 `docs/data-schema.md`
- 明确所有图片字段是否统一为数组
- 明确重复图片对象的去重与计数口径
- 给 ENTER1、ENTER2、ENTER3 和 `meta.json` 提供真实示例

### STEP 3：实现同步，但暂不修改页面

- 新建 `excel/`
  - 放置/复制三份正式 Excel 数据源（需在实施时确定保留附件原件还是迁移后仅维护一份）
- 新建 `scripts/sync_excel.py`
- 新建 `scripts/excel_reader.py`
- 新建 `scripts/image_extractor.py`
- 新建 `scripts/validators.py`
- 新建 `requirements.txt`
- 生成 `data/basic_information.json`
- 生成 `data/certification_marks.json`
- 生成 `data/reference_links.json`
- 生成 `data/meta.json`
- 生成/完整重建 `assets/generated/enter1/`
- 生成/完整重建 `assets/generated/enter2/`

以下文件在 STEP 3 不修改：

- `index.html`
- `logo.png`
- `img_new_hd/`
- 现有附件和人工素材

`index.html` 的 fetch 接入、回归测试、README 和 GitHub Pages 配置分别留到后续 STEP 4–8。
