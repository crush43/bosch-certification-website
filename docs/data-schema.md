# 博世认证网站数据 Schema

本文定义 Excel 同步程序生成、网站读取的 JSON 契约。业务人员只维护配置的数据源目录中的三份 Excel；`data/` 和 `assets/generated/` 均由同步程序完整生成。

## Excel 数据源配置

- 项目提交 `config.example.json` 作为安全示例，不在其中填写真实公司路径。
- 未创建本地配置时，同步器默认读取 `./excel`。
- 可用不提交版本库的 `config.local.json` 设置数据源，适合每台电脑配置自己的共享盘、同步盘或 UNC 路径。
- `excelSource` 可为相对项目根目录的路径，也可为绝对路径；命令行 `--excel-dir` 具有最高优先级。旧版 `config.json` 仍可读取，但新部署不再推荐使用。
- 同一次同步只读取一个目录，三份正式 Excel 必须都来自这个目录，从而维持单一数据源。

## 通用约定

- 编码：UTF-8，无 BOM。
- JSON 使用 2 空格缩进，文件末尾保留换行。
- 业务文本不自动翻译。三语言对象固定包含 `zh`、`en`、`de`；无来源的语言写空字符串。
- 页面取值回退顺序：当前语言 → 中文 → 英文 → 德文 → 空字符串。
- 所有字符串去除首尾空白；Excel 中仅包含 `/` 的值转换为空。
- 所有图片字段都是数组。无图片时为 `[]`，不得为 `null`、`""` 或 `/`。
- 图片路径使用相对于网站根目录的 `/` 分隔路径。
- ID 为确定性 ID。Excel 插入或移动行不会改变同一业务记录的 ID。

## `data/basic_information.json`

顶层类型：`BasicInformationRecord[]`

```json
[
  {
    "id": "e1_87ae895894e0",
    "country": { "zh": "中国", "en": "", "de": "" },
    "category": { "zh": "电动工具", "en": "", "de": "" },
    "product": { "zh": "电锤", "en": "", "de": "" },
    "powerType": "Corded",
    "example": [
      "assets/generated/enter1/e1_87ae895894e0_example_01.png"
    ],
    "model": "GBH6-42VB",
    "bareModel": "3611B78180",
    "specs": "220V 50Hz 1300W",
    "dateCode": "MM/YYYY",
    "cert": [
      "assets/generated/enter1/e1_87ae895894e0_cert_01.png"
    ],
    "eco": [
      "assets/generated/enter1/e1_87ae895894e0_eco_01.png",
      "assets/generated/enter1/e1_87ae895894e0_eco_02.png"
    ],
    "origin": [
      "assets/generated/enter1/e1_87ae895894e0_origin_01.png"
    ],
    "class2": [
      "assets/generated/enter1/e1_87ae895894e0_class2_01.png"
    ],
    "manufacturer": [
      "assets/generated/enter1/e1_87ae895894e0_manufacturer_01.png"
    ],
    "weee": [
      "assets/generated/enter1/e1_87ae895894e0_weee_01.png"
    ],
    "manual": [
      "assets/generated/enter1/e1_87ae895894e0_manual_01.png"
    ],
    "ip": "",
    "protect": [],
    "other": [],
    "extraFields": [
      {
        "column": 20,
        "label": { "zh": "新增字段", "en": "", "de": "" },
        "value": { "zh": "新增内容", "en": "", "de": "" },
        "images": []
      }
    ]
  }
]
```

字段约束：

| 字段 | 类型 | 来源/约束 |
|---|---|---|
| `id` | string | `e1_` + SHA-256 前 12 位；输入为 country、category、product、powerType、model 的规范化值 |
| `country` | LocalizedText | 必填，Excel `国家` |
| `category` | LocalizedText | 必填，Excel `产品类别` |
| `product` | LocalizedText | 必填，Excel `产品名称` |
| `powerType` | string | `Corded`、`Cordless` 或空 |
| `example` | string[] | Excel `示例`；页面主图使用第 1 张 |
| `model` | string | Excel `型号` |
| `bareModel` | string | Excel `裸机号`，始终按文本处理 |
| `specs` | string | Excel `参数`，拼接富文本全部 text runs |
| `dateCode` | string | Excel `生产年月`，按文本处理 |
| `cert` | string[] | Excel `认证标志` |
| `eco` | string[] | Excel `环保标志`，允许同一单元格多图 |
| `origin` | string[] | Excel `原产地信息` |
| `class2` | string[] | Excel `Class II 标志` |
| `manufacturer` | string[] | Excel `制造商/生产者信息` |
| `weee` | string[] | Excel `WEEE标志` |
| `manual` | string[] | Excel `阅读说明书` |
| `ip` | string | Excel `IP等级` |
| `protect` | string[] | Excel `防护标志` |
| `other` | string[] | Excel `其他特殊标签` |
| `extraFields` | ExtraField[] | ENTER1 中不属于 A–S 固定字段的新增列，按 Excel 从左到右顺序生成，并在页面字段 13 后依次展示 |

`ExtraField` 结构：

- `column`：Excel 实际列号，用于保持顺序和生成稳定图片文件名。
- `label`：新增列的表头，按 LocalizedText 保存；当前来源只写中文。
- `value`：该记录在新增列中的单元格文字，按 LocalizedText 保存。
- `images`：锚定在该记录、新增列单元格中的全部图片；同锚点不同内容全部保留，相同内容去重。

新增列无需修改同步代码或页面模板。同步后，网站会把它们作为新的“铭牌各区域详解”卡片，按 Excel 列顺序排列在原有 13 个区块之后。新增列必须有非空且唯一的表头。

## `data/certification_marks.json`

顶层类型：`CertificationMarkRecord[]`

```json
[
  {
    "id": "e2_161111b021",
    "country": { "zh": "欧盟", "en": "", "de": "" },
    "name": "CE",
    "drawing": "161111B021",
    "image": [
      "assets/generated/enter2/e2_161111b021_01.png"
    ],
    "notes": {
      "zh": "1.尺寸: 高度≥5mm\n2.格式: 如果CE标志缩小或放大，必须遵守图示比例\n3.位置1: CE标志的各个组成部分必须具有相同的垂直尺寸\n4.位置2: CE标志必须贴在制造商名称附近",
      "en": "",
      "de": ""
    },
    "products": {
      "zh": "手持式工具，移动式工具，草坪和园林机械，家用电器，测量工具",
      "en": "",
      "de": ""
    }
  }
]
```

字段约束：

| 字段 | 类型 | 来源/约束 |
|---|---|---|
| `id` | string | 优先为 `e2_` + 规范化图纸编号；图纸编号为空时使用稳定 hash |
| `country` | LocalizedText | 必填，Excel `国家` |
| `name` | string | 必填，Excel `标志` |
| `drawing` | string | Excel `图纸编号`；空值产生 Warning |
| `image` | string[] | Excel `标志示意图`，允许多图 |
| `notes` | LocalizedText | Excel `关键备注`，保留换行 |
| `products` | LocalizedText | Excel `适用产品` |

`nameCn` 不属于数据源契约，因为 Excel 没有该字段，且第一阶段禁止编造业务翻译。

## `data/reference_links.json`

顶层类型：`ReferenceLinkRecord[]`

```json
[
  {
    "id": "e3_2fc33d5ae526",
    "key": "PT",
    "title": "PT/ECS",
    "url": "https://connect.bosch.com/blogs/03687740-2d27-4f8c-a670-b4adda24712b?lang=en_us"
  }
]
```

字段约束：

| 字段 | 类型 | 来源/约束 |
|---|---|---|
| `id` | string | `e3_` + title、URL 规范化后的 SHA-256 前 12 位 |
| `key` | string | 已知名称映射为 `PT`、`News`、`EUDoC`；未知名称生成 ASCII key |
| `title` | string | 必填，Excel A 列 |
| `url` | string | 必填，Excel B 列；必须以 `http://` 或 `https://` 开头 |

新增未知链接不需要增加 i18n key。STEP 4 中页面将直接显示 `title`，并使用默认图标和通用链接样式。

## `data/meta.json`

```json
{
  "generatedAt": "2026-09-10T21:30:00+08:00",
  "status": "success",
  "sources": {
    "basicInformation": {
      "file": "ENTER 1-Basic Information.xlsx",
      "modifiedAt": "2026-09-10T21:20:00+08:00",
      "sha256": "...",
      "records": 4
    },
    "certificationMarks": {
      "file": "ENTER 2-Certification Mark.xlsx",
      "modifiedAt": "2026-09-10T21:20:00+08:00",
      "sha256": "...",
      "records": 7
    },
    "referenceLinks": {
      "file": "ENTER 3-Reference Link.xlsx",
      "modifiedAt": "2026-09-10T21:20:00+08:00",
      "sha256": "...",
      "records": 3
    }
  },
  "images": {
    "enter1Objects": 32,
    "enter1Logical": 32,
    "enter1DuplicatesRemoved": 0,
    "enter2Objects": 7,
    "enter2Logical": 7,
    "enter2DuplicatesRemoved": 0,
    "totalLogical": 39
  },
  "warnings": 0
}
```

图片数量动态取本次成功同步实际输出数量，示例数字不是固定校验条件。

## 图片去重与排序

每个图片对象记录：Sheet、anchor 行、anchor 列、行列偏移、drawing 顺序、媒体关系和原始内容 SHA-256。

- 同 Sheet + 同 anchor 单元格 + 同内容 hash：重复对象，只保留一次并输出 Warning。
- 同 anchor 单元格 + 不同内容 hash：合法多图，全部保留。
- 不同 anchor 单元格复用同一媒体：属于不同业务记录/字段，各自导出稳定路径。
- 同一字段的图片按 anchor 偏移和 drawing 顺序稳定排序，文件名使用 `_01`、`_02`。

## 同步事务与多人维护

1. 同步器先检查三份正式 Excel 是否存在，并拒绝在发现 Excel 临时锁文件时发布。
2. 将 Excel 复制到本次独立构建目录，并核对复制前后文件大小、修改时间和 SHA-256，防止读取正在保存的文件。
3. 在构建目录生成完整 JSON、图片和 meta。
4. 执行表头、字段、URL、ID、图片关系、JSON 路径和图片解码校验。
5. 只有零 Error 时才用带回滚的目录替换发布 `data/` 与 `assets/generated/`。
6. 任一步失败均保留上一次正式数据，并写失败日志。

同步日志不得包含账号、令牌或其他敏感信息。

### STEP 6 生产配置

```json
{
  "excelSource": "S:/CertificationWebsite/Data",
  "productionMode": true,
  "archiveSnapshots": true,
  "archiveDirectory": "S:/CertificationWebsite/Archive"
}
```

- 生产模式拒绝使用仓库内的 `./excel` 测试源。
- 每次运行只解析 `.build/` 中经过校验的本地 snapshot。
- 本机日志记录源路径、大小、修改时间、snapshot 时间和 SHA-256。
- 网站公开数据 `data/meta.json` 刻意不包含源目录路径。
- 开启归档后，三份已验证工作簿和 `snapshot-manifest.json` 保存到带时间戳的归档目录。
- 对应的 `~$` 锁文件、snapshot 期间的大小或修改时间变化都会在替换正式数据前终止同步。

## 后续模块与数据源扩展原则

- ENTER1 当前只实现“铭牌信息”Sheet。未来包装、说明书、警告标签等模块应各自拥有明确的 Sheet、Schema、验证规则和 JSON 输出；在业务表结构确认前不预造数据，也不把模块逻辑硬编码进页面。
- 新模块沿用稳定 ID、图片数组、动态计数、临时构建、完整校验、原子发布和失败回滚原则。
- 未来接入共享盘、OneDrive 或 SharePoint 时，同步器仍只消费一个已挂载或已同步到本机的正式目录；远端下载/鉴权应作为独立上游步骤，不把账号或令牌写进本项目配置和日志。
- 无论数据源位于本地还是共享位置，Excel 始终是业务事实来源，JSON 与导出图片始终是可重建产物。
