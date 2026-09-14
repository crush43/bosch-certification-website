# 《认证网站》STEP 4 最终结果

## 完成状态

STEP 4 已完成。

网站已从 HTML 内部硬编码数据切换为读取 Excel 同步生成的 JSON 数据。目前已经形成以下完整链路：

```text
Excel
  ↓
scripts/sync_excel.py
  ↓
data/*.json + assets/generated/*
  ↓
index.html 通过 fetch() 加载
  ↓
网站显示最新内容
```

本阶段没有进入 GitHub Pages、SharePoint、共享盘或自动发布，这些属于后续 STEP 5。

---

## A. index.html 修改内容

本阶段只对 `index.html` 做了 JSON 数据接入所需的最小改造：

- 增加异步 JSON 初始化函数。
- 增加 Loading 状态。
- 增加中文、英文、德文加载失败提示。
- 增加首页“最后更新”显示。
- 适配新的 JSON 字段名及图片数组。
- 保留原有 Bosch 视觉风格和整体页面结构。
- 保留 HOME、ENTER1、ENTER2、ENTER3 和顶部导航。
- 保留中文、English、Deutsch 切换。
- 保留筛选、搜索、展开、折叠和图片放大功能。

没有引入 React、Vue、Next.js 或其他前端框架。

---

## B. 删除的硬编码业务数据

原 `index.html` 中以下三组正式业务数据已经彻底删除：

```javascript
const D1 = [...];
const D2 = [...];
const D3 = [...];
```

旧图片路径前缀也已删除：

```javascript
const P = 'img_new_hd/';
```

现在页面只保留空的数据容器：

```javascript
let D1 = [];
let D2 = [];
let D3 = [];
let META = null;
```

网站不存在 JSON 和 HTML 硬编码业务数据并存的问题。Excel 同步生成的 JSON 是网站唯一的正式业务数据来源。

---

## C. JSON 加载流程

页面启动时由 `loadAppData()` 加载：

```text
./data/basic_information.json
./data/certification_marks.json
./data/reference_links.json
./data/meta.json
```

三个核心 JSON 使用统一的 `fetchJson()` 加载，并检查 `response.ok`：

- `basic_information.json`
- `certification_marks.json`
- `reference_links.json`

成功初始化顺序如下：

```text
显示 Loading
  ↓
加载 JSON
  ↓
赋值 D1 / D2 / D3 / META
  ↓
applyLang()
  ↓
go('home')
  ↓
隐藏 Loading，网站可用
```

`meta.json` 是非关键资源。meta 加载失败时网站仍然可以正常使用。

---

## D. Loading 和错误状态

已实现并实际测试：

- 数据加载期间显示“数据加载中...”。
- 数据加载成功后 Loading 自动隐藏。
- 任一核心 JSON 加载失败时页面不会白屏。
- 页面显示普通用户可理解的错误信息，不显示技术堆栈。
- 详细错误通过 `console.error()` 输出到浏览器控制台。
- `meta.json` 加载失败只通过 `console.warn()` 提示，不阻止网站启动。

错误提示：

```text
中文：数据加载失败，请刷新页面或联系认证工程师。

English：Failed to load data. Please refresh the page or contact the certification engineer.

Deutsch：Daten konnten nicht geladen werden. Bitte aktualisieren Sie die Seite oder wenden Sie sich an den Zertifizierungsingenieur.
```

---

## E. ENTER1 测试结果

以下四条指定路径均已在真实浏览器中完成回归测试，每条路径都只返回一条正确记录：

```text
中国
→ 电动工具
→ 电锤
→ Corded
→ GBH6-42VB
```

```text
欧盟
→ 电动工具
→ 角磨
→ Cordless
→ GWS 18V-15 S
```

```text
欧盟
→ 家用电器
→ 吸尘器
→ Corded
→ GAS 12-25 PL
```

```text
乌克兰
→ 电动工具
→ 台锯
→ Corded
→ GTS 635-216
```

字段兼容改造结果：

- 旧 `corded` 已改为读取 `powerType`。
- 旧 `mfr` 已改为读取 `manufacturer`。
- `example`、`cert`、`eco`、`origin`、`class2`、`manufacturer`、`weee`、`manual`、`protect`、`other` 均按图片数组处理。
- 完整铭牌使用 `example[0]`。
- 空图片数组显示“暂无图片”，不会产生 JavaScript 错误。
- 图片放大功能正常。

---

## F. K3 多图测试结果

中国电锤记录的环保标志对应 Excel K3。

测试结果：

```text
JSON 图片数量：2
网页显示数量：2
唯一图片数量：2
图片放大：正常
```

两张合法图片均正常显示，没有只显示第一张，也没有重复显示同一张图片。

---

## G. L5 单图测试结果

欧盟吸尘器记录的原产地信息对应 Excel L5。

测试结果：

```text
JSON 图片数量：1
网页显示数量：1
```

网页只显示一次，不受旧版历史重复记录影响。

---

## H. ENTER2 测试结果

以下 7 项认证标志均正常显示：

1. CE
2. CCC
3. China RoHS II for compliance
4. China RoHS II for noncompliance
5. UL
6. ETL
7. CSA

测试结果：

- 7 条 JSON 记录正常加载。
- 7 张认证卡片正常显示。
- 7 张认证图片正常显示。
- 关键词搜索正常。
- 国家筛选正常。
- 适用产品筛选正常。
- 单张卡片展开正常。
- 全部展开后有 7 张展开卡片。
- 全部折叠后展开卡片数量为 0。

搜索内容覆盖：

- 标志名称
- 国家
- 图纸编号
- 关键备注
- 适用产品

兼容改造结果：

- 旧 `img` 已改为读取 `image`。
- 卡片主图使用 `image[0]`。
- 缺少图片时显示空图片状态，不会报错。
- 页面不再依赖 `nameCn` 必须存在。
- 展开状态使用 `drawing || id`，避免空 drawing 导致多张卡片共用状态。

---

## I. ENTER3 测试结果

正式数据中的以下链接均正常显示：

- PT/ECS
- News
- EUDoC

页面现在优先显示 Excel/JSON 中的 `title`，不再要求每个链接都必须存在 i18n key。

未知 key 测试结果：

```text
标题：Test Link
图标：🔗
链接：https://example.com
```

即使没有对应的 `lkTestLink` 翻译项，链接卡片仍然可以正常显示和打开。

---

## J. Excel → JSON → Website 端到端测试

已完成一次真实端到端测试，不是直接手改 JSON。

测试步骤：

1. 备份正式 `ENTER 3-Reference Link.xlsx`。
2. 在 Excel 中临时新增：

   ```text
   Test Link
   https://example.com
   ```

3. 运行 `scripts/sync_excel.py`。
4. `reference_links.json` 从 3 条自动变为 4 条。
5. 浏览器刷新后，无需修改 `index.html`，网站自动出现 `Test Link`。
6. 恢复原始 Excel。
7. 再次运行同步。
8. JSON 恢复为 3 条。
9. 浏览器刷新后，`Test Link` 自动消失。

Excel 恢复后的 SHA-256 与测试前完全一致：

```text
AB461B6C29DA76CF0138F8C1AC43E50FB494A761B10658A7FD8FE5FEA8F75381
```

这证明以下链路已经真实成立：

```text
Excel 修改
→ 运行同步
→ JSON 自动更新
→ 网站刷新后自动显示最新内容
```

---

## K. 浏览器 Console 和 Network 检查

最终真实浏览器检查结果：

```text
JavaScript 语法错误：0
Console Error：0
JavaScript Exception：0
核心 JSON：HTTP 200
meta.json：HTTP 200
业务图片：39 张
图片缺失：0
业务请求 4xx/5xx：0
```

浏览器会自动请求项目中不存在的 `favicon.ico`，因此本地服务器日志中有一条与业务无关的 favicon 404。这不会影响网站功能、JSON 或图片加载。

---

## L. 已知限制和注意事项

### 1. 必须通过 HTTP 打开

由于页面使用 `fetch()` 加载 JSON，不能再把双击 `index.html`、使用 `file://` 作为正式运行方式。

必须使用 HTTP Server。

### 2. 业务语言回退

当前 Excel 主要提供中文业务内容。切换 English 或 Deutsch 后，没有对应翻译的业务字段会按照以下顺序回退：

```text
当前语言
→ 中文
→ 英文
→ 德文
→ 空字符串
```

UI 菜单和固定说明仍然有中、英、德三种语言。

### 3. 当前不是自动监听

保存 Excel 后不会立即自动更新网站。每次修改 Excel 后，需要人工运行一次同步命令。

---

## M. STEP 5 建议

后续 STEP 5 可以考虑：

1. 提供双击即可执行的 Excel 同步与本地网站启动入口。
2. 设计 GitHub Pages 或其他静态托管发布流程。
3. 配置共享盘、OneDrive 或 SharePoint 的正式 Excel 数据源。
4. 增加发布前校验和正式/测试环境区分。
5. 设计自动同步频率、权限和失败通知方式。

本阶段没有执行以上内容。

---

# 日常更新操作说明

## 1. 修改 Excel

在 `excel/` 目录中按照原有格式修改或新增内容：

```text
excel/ENTER 1-Basic Information.xlsx
excel/ENTER 2-Certification Mark.xlsx
excel/ENTER 3-Reference Link.xlsx
```

注意：

- 不要修改 Sheet 名称。
- 不要修改表头名称。
- 按现有列结构继续增加数据行。
- 图片放入对应记录、对应字段的单元格。
- 没有内容时留空，不要填写 `/`。
- ENTER3 的 URL 必须以 `http://` 或 `https://` 开头。

保存并关闭 Excel 后再执行同步。

## 2. 执行同步

在项目根目录运行：

```powershell
python scripts/sync_excel.py
```

看到以下信息表示同步成功：

```text
Validation: PASSED
JSON generated successfully.
Formal data replaced successfully.
```

如果同步校验失败，正式网站数据不会被覆盖，网站会继续使用上一次成功的数据。

## 3. 启动本地网站

在项目根目录运行：

```powershell
python -m http.server 8080
```

浏览器访问：

```text
http://localhost:8080
```

修改 Excel 并成功同步后，刷新浏览器即可看到最新内容。

---

## 最终结论

目前已经可以按照原 Excel 格式新增或修改内容，然后运行一次同步脚本，使网站读取最新 JSON 和图片。

正式更新流程为：

```text
按照原格式修改 Excel
→ 保存并关闭 Excel
→ 运行 python scripts/sync_excel.py
→ 确认 Validation: PASSED
→ 刷新网站
```
