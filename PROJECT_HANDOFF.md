# Bosch Certification Website / 《认证网站》项目交接基线

> 本文件是本项目后续 ChatGPT / Codex 新聊天的项目状态主索引。
>
> 最后核对日期：2026-09-14  
> 本地项目：`E:\bosch`  
> GitHub：`crush43/bosch-certification-website`  
> 分支：`main`  
> 仓库可见性：`Private`

## 1. 交接文件用途

本文件用于在新聊天、新 Codex 会话或更换维护人员时恢复项目上下文。继续工作前必须先核对实际项目文件、最新 STEP 最终报告和 Git 状态；本文件不是覆盖代码事实的替代品。

项目不是从零开始的网站。当前原型、Excel 数据结构、同步器、JSON 数据层、生产安全机制和 Git 基础设施均已建立。后续工作必须在现有成果上继续，避免重建网站或改变已经验收的数据结构。

## 2. 项目身份与 Git 基线

| 项目 | 当前值 |
| --- | --- |
| 项目名称 | Bosch Certification Website / 《认证网站》 |
| 本地目录 | `E:\bosch` |
| GitHub owner | `crush43` |
| GitHub repo | `bosch-certification-website` |
| Remote | `https://github.com/crush43/bosch-certification-website.git` |
| Branch | `main` |
| Visibility | `Private` |
| STEP 6 基线 commit | `032f8fc81106de302fa3afcebdfca461c9ce4dc3` |
| STEP 6 commit message | `feat: add controlled shared-Excel production workflow` |
| STEP 6 核对时 remote main | 与本地 `HEAD` 一致 |

本文件创建后的实际最新 commit 应以 `git log` 为准。不要将仓库自动改为 Public。

## 3. PROJECT ROADMAP

| STEP | 内容 | 状态 |
| --- | --- | --- |
| STEP 1 | Data Mapping / 数据映射 | COMPLETED |
| STEP 2 | JSON Schema | COMPLETED |
| STEP 3 | Excel Sync Engine / Excel → JSON 与图片同步器 | COMPLETED |
| STEP 4 | Website JSON Integration | COMPLETED AND VERIFIED |
| STEP 5 | Git / GitHub / Deployment Foundation | PARTIALLY COMPLETED |
| STEP 6 | Multi-user Excel / Production Safety | COMPLETED AND VERIFIED |
| STEP 7 | Production Deployment Decision & Go-Live / 正式部署环境确定与上线 | NOT STARTED — NEXT |
| STEP 8 | Real Bosch Shared Data Source Integration | PLANNED |
| STEP 9 | UAT / Failure / Recovery Testing | PLANNED |
| STEP 10 | Production Handover / Operations / Training | PLANNED |
| STEP 11 | Advanced Automation | OPTIONAL |

STEP 7 不是默认“部署 GitHub Pages”。正式平台尚未决定，可能是 GitHub Pages、Bosch Internal Web Server、SharePoint / Microsoft 365，或其他 Bosch 批准的平台。

STEP 8 将接入真实 Bosch Shared Source，可能采用 SharePoint 同步目录、OneDrive for Business 同步目录或网络共享盘。Microsoft Graph API 不是当前默认方案。

STEP 11 只属于可选增强，未来可能包括定时同步、自动部署、SharePoint API、Microsoft Graph、CI/CD、通知与监控；当前不得提前实现。

## 4. STEP 1 — Data Mapping

状态：COMPLETED

`DATA_MAPPING.md` 已完成，ENTER1、ENTER2、ENTER3 的 `Excel → JSON → 页面` 映射已经确定。

图片业务字段不能根据 Excel 内部 media filename 判断，必须结合以下信息：

```text
Sheet + Anchor + Header
```

关键规则：

- 图片数量不得写死，每次同步必须动态扫描实际 Excel。
- ENTER1 的 K3 同一单元格有两张不同内容的图片，属于合法多图，必须全部保留。
- `same sheet + same anchor + same content hash`：判定为 duplicate，去重并产生 warning。
- `same sheet + same anchor + different hash`：判定为合法多图，全部保留。
- ENTER1 L5 历史上曾存在重复图片对象，用户已从最新版 Excel 删除该重复对象。`DATA_MAPPING.md` 中旧的 33 项清单是历史取证，不能作为当前固定数量。

## 5. STEP 2 — JSON Schema

状态：COMPLETED

核心网站数据：

- `data/basic_information.json`
- `data/certification_marks.json`
- `data/reference_links.json`
- `data/meta.json`

主要设计：

- ENTER1 的所有图片字段采用数组，包括 `example`。
- 稳定 ID 使用稳定业务字段生成，不能依赖 Excel row number。
- 无可靠来源翻译时不得自动编造英文或德文翻译。
- 前端允许语言 fallback。
- 完整字段与样例以 `docs/data-schema.md` 和实际 JSON 为准。

## 6. STEP 3 — Excel Sync Engine

状态：COMPLETED

已经建立以下安全同步链：

```text
Excel
  ↓
Snapshot / Temp Build
  ↓
Parse
  ↓
Validation
  ↓
Image Extraction
  ↓
JSON + Generated Images
  ↓
Atomic / Safe Replacement
```

同步失败不得覆盖上一版正式 `data/` 和 `assets/generated/`。

当前实际脚本：

- `scripts/sync_excel.py`：同步总入口、构建与安全替换。
- `scripts/excel_reader.py`：Excel 读取、清洗、快照与哈希支持。
- `scripts/image_extractor.py`：Excel 图片锚点读取、去重与导出。
- `scripts/validators.py`：表头、记录、URL 和生成结果校验。
- `scripts/validate_site.py`：发布前静态网站数据及资源校验。
- `scripts/record_publish.py`：成功推送后的本地发布历史。

## 7. STEP 4 — Website JSON Integration

状态：COMPLETED AND VERIFIED

`index.html` 已取消将 `D1`、`D2`、`D3` 硬编码业务数据作为权威源。页面现在通过 `fetch()` 加载四个 JSON 文件，并提供 Loading、错误提示和 `meta.json` 更新时间显示。

当前验收基准：

| 模块 | 记录数 |
| --- | ---: |
| ENTER1 | 4 |
| ENTER2 | 7 |
| ENTER3 | 3 |
| 页面引用图片 | 39 |

已完成真实端到端测试：

```text
Excel 临时新增 Test Link
→ sync
→ JSON 增加
→ 网站自动显示

恢复 Excel
→ 再次 sync
→ JSON 与网站恢复
```

这证明 `Excel → JSON → Website` 链路真实成立。详细验收见 `STEP4_FINAL_REPORT.md` 和 `STEP6_FINAL_REPORT.md`。

## 8. STEP 5 — Git / GitHub / Deployment Foundation

状态：PARTIALLY COMPLETED

子状态：

| 项目 | 状态 |
| --- | --- |
| Local Git | COMPLETED |
| GitHub Repository | COMPLETED |
| Push main | COMPLETED |
| GitHub Pages Online Deployment | NOT COMPLETED |

当前仓库为 `crush43/bosch-certification-website`，默认分支为 `main`，仓库保持 Private，代码已经成功推送。

当前实际部署基础设施包括：

- `.github/workflows/deploy.yml`
- `.gitignore`
- `config.example.json`
- `sync_website.bat`
- `preview_website.bat`
- `publish_website.bat`
- `scripts/validate_site.py`
- `README.md`

`.github/workflows/deploy.yml` 是 GitHub Pages 的可选部署工作流。工作流存在不代表 Pages 已启用或已验收。GitHub Pages 当前状态仍是 NOT DEPLOYED，因此 STEP 5 不能标为全部完成。

## 9. STEP 6 — Shared Excel / Production Safety

状态：COMPLETED AND VERIFIED

以 `STEP6_FINAL_REPORT.md` 和实际代码为准，已完成：

1. 外部共享 Excel 生产模式。
2. `config.local.json` 指向外部 Excel 目录，支持本地绝对路径及 Windows UNC 路径。
3. 生产模式拒绝项目内 `./excel`，隔离 TEST EXCEL 与 PRODUCTION EXCEL。
4. 同步前检查 Excel `~$` 临时锁文件。
5. 为三份 Excel 建立独立 `.build` snapshot，解析过程只读取 snapshot。
6. 复制前后校验 size 与 mtime，并比较源文件和 snapshot 的 SHA-256。
7. 哈希后再次确认源文件状态，检测同步过程中发生的变化。
8. 校验成功后才安全替换正式 JSON 和 generated assets。
9. 可选 Archive：原子写入三份已验证 Excel 快照和 `snapshot-manifest.json`。
10. 发布开始前要求 Git 工作区干净，并执行 `git pull --rebase origin main`。
11. 发布前要求本地预览和人工确认。
12. 只暂存批准文件，执行 staged diff 检查，并再次确认 commit 与 push。
13. 推送后 fetch 并验证远程 `origin/main`。
14. 成功生产同步且本地与远程一致后，向本机 `logs/publish-history.jsonl` 写发布历史。
15. 本地配置、日志、临时文件、Archive、生产 Excel 和常见凭据文件均由 `.gitignore` 排除。
16. 已形成多人维护、异常处理、回滚和部署选择文档。

### STEP 6 验证结果

- 网站校验：ENTER1 = 4、ENTER2 = 7、ENTER3 = 3、Images = 39。
- 模拟共享源中临时增加 ENTER3 记录后，生产同步成功，网站真实显示；恢复 Excel 后网站恢复。
- Excel 被占用时同步安全停止，正式数据和生成图片不变化。
- 源 Excel 在 snapshot 过程中变化时同步中止。
- 生产模式不会误读项目内测试 Excel。
- 生产模式缺少外部配置时会阻止执行。
- Archive 测试成功生成三份 Excel 和 manifest；测试归档已经清理。
- 发布历史模拟测试成功；测试日志已经清理。
- Git 未跟踪 Excel、ZIP、本地配置、日志、snapshot、Archive 或临时目录。
- STEP 6 未修改网站现有 UI、ENTER1/2/3 业务结构或数据结构。

### STEP 6 交付文件

- `STEP6_FINAL_REPORT.md`
- `docs/production-architecture.md`
- `docs/operations.md`
- `docs/deployment-options.md`
- `README.md`
- `tests/test_sync_safety.py`

## 10. 目标生产架构

```text
Bosch SharePoint
/ OneDrive for Business
/ Teams-backed SharePoint
/ Bosch Network Shared Drive
        ↓
Single Source of Truth
唯一正式 Excel
        ↓
Snapshot
        ↓
Validation
        ↓
Excel Parser
        ↓
JSON + Generated Images
        ↓
Preview
        ↓
Manual Approval
        ↓
Git / Deployment Platform
        ↓
Website
```

Excel 数据层、同步器、生成网站文件和托管平台保持解耦。更换托管平台时不应重写 Excel 解析器或已经验收的网站数据结构。

## 11. Single Source of Truth 与角色

未来正式 Excel 只能有一套，多名业务人员共同维护同一个正式数据源。

禁止以下模式：

```text
A 本地正式 Excel
B 本地正式 Excel
C 本地正式 Excel
→ 分别发布
```

角色职责：

- 业务维护人员：只维护共享位置中的正式 Excel，不修改网站代码。
- 发布人员：执行 Sync、Validation、Preview 和 Publish。
- 开发 / IT：负责代码、Git、部署平台、权限和故障恢复。

第一阶段采用指定同步电脑或指定发布人员的单点发布方式，不实现分布式发布锁，也不将“保存 Excel”与自动发布绑定。

## 12. 代码与业务数据分离

- Git 仓库管理代码和允许进入版本库的生成网站数据。
- Shared Drive / SharePoint 管理唯一正式 Excel。
- 不要把整个 Git 项目放在多人共享盘上共同编辑。
- 生产 Excel 不应成为普通 Git 业务源。
- `data/` 和 `assets/generated/` 是网站发布内容，但其公开性必须在部署前单独审核。

## 13. SECURITY BLOCKER / DECISION POINT

状态：BLOCKED（仅针对“确定正式平台并发布真实数据到生产环境”）

仓库目前保持 Private。仓库中的网站运行数据可能包含 Bosch 内部链接、认证图片和生成后的业务数据。

在执行以下任一动作前：

- 将仓库转为 Public；
- 启用面向公网的 GitHub Pages；
- 将真实 Bosch 数据部署到其他公网环境；

必须先完成：

1. 业务数据公开性审核。
2. Bosch IT / Information Security 确认。
3. 正式托管平台及访问控制决定。

不得因为仓库内已经存在 Pages workflow，就推断 GitHub Pages 已批准。Private Git 仓库也不等于最终网站天然具有内部访问控制。

## 14. 部署平台决策

GitHub Pages 当前只能视为 OPTIONAL deployment option，不是已确定的正式生产平台。

候选方案：

| 方案 | 当前定位 |
| --- | --- |
| GitHub Pages | OPTIONAL；静态站点兼容度高，但公开性与企业账户能力必须审核 |
| Bosch Internal Web Server | 候选；适合内网访问控制，需 IT 配置 HTTPS、权限、域名与运维 |
| SharePoint / Microsoft 365 | 候选；身份权限可复用，但完整静态网站和脚本策略需实测 |
| 其他 Bosch 批准的平台 | 候选；只要支持 HTML、JSON 和图片即可复用现有产物 |

选择依据和限制见 `docs/deployment-options.md`。不得替用户或 Bosch IT 提前决定。

## 15. 已知限制与待确认事项

- 正式 Excel 的最终共享位置及权限组尚未确认。
- 指定同步电脑和发布负责人尚未确认。
- Archive 的正式位置、保留周期、访问权限和备份策略尚未确认。
- GitHub Private 仓库是否允许长期保存当前生成 JSON、图片及内部链接，需要 Bosch IT / 信息安全确认。
- GitHub Actions 是否允许使用尚未确认。
- 正式托管平台和访问范围尚未确认。
- 如要求仅内部访问，身份认证和网络边界尚未确定。
- 正式发布审批、审计责任人、HTTPS、域名、日志和灾备要求尚未确定。
- 当前没有接入真实 Bosch 共享 Excel；STEP 6 使用的是隔离的模拟共享源测试。

## CURRENT EXACT STOP POINT

```text
STEP 6:
COMPLETED AND VERIFIED

Git:
PUSHED

Remote main:
SYNCED

Repository:
PRIVATE

GitHub Pages:
NOT DEPLOYED

STEP 7:
NOT STARTED

CURRENT NEXT ACTION:
STEP 7 — 正式部署环境确定与上线
```

在确认部署平台和数据公开性之前，不得直接发布真实 Bosch 数据到公网。未经用户确认，不得进入 STEP 7。

## 17. STEP 7 启动条件

STEP 7 的目标是“确定正式部署环境并完成上线”，不是预设部署 GitHub Pages。

启动前至少需要用户或 Bosch 相关负责人确认：

1. 网站数据允许的访问范围：公网、Bosch 内网或指定账号。
2. Bosch IT / 信息安全批准的托管平台。
3. 当前生成 JSON、图片和内部链接能否进入该平台。
4. 谁负责正式部署验收与上线批准。

在以上决定完成前，可以继续做只读核对和非敏感方案比较，但不得发布真实 Bosch 数据到公网。

## NEW CHAT RECOVERY PROTOCOL

以后开启新的 ChatGPT 聊天时，用户应上传：

1. `PROJECT_HANDOFF.md`（必需）。
2. 最新的 STEP FINAL REPORT（如方便，建议同时上传）。

用户第一句话：

> 继续《认证网站》项目。PROJECT_HANDOFF.md 是当前项目交接基线。请先恢复项目状态，不要直接开始开发。

新聊天必须：

1. 先读取 `PROJECT_HANDOFF.md`。
2. 告诉用户当前 STEP 状态。
3. 告诉用户 CURRENT EXACT STOP POINT。
4. 告诉用户 NEXT STEP。
5. 指出当前 Blocker / Decision Point。
6. 未经用户确认，不得自动进入下一 STEP。

## 19. Codex 新会话恢复协议

Codex 新会话必须优先读取：

1. `PROJECT_HANDOFF.md`
2. 最新 STEP FINAL REPORT
3. `DATA_MAPPING.md`
4. `README.md`

然后检查：

```text
git status
git log
实际代码与目录结构
```

如果实际状态与本文冲突，以事实优先级处理，并先向用户说明差异。

## 20. 事实优先级

发生冲突时：

1. Actual Project Files / Code
2. Latest STEP FINAL REPORT
3. Git Status / Git Log
4. `PROJECT_HANDOFF.md`
5. Old ChatGPT / Codex Memory

旧聊天记忆不得覆盖最新代码、最新报告或 Git 事实。

## 21. PROJECT_HANDOFF 更新规则

每完成一个 STEP，必须更新同一个 `PROJECT_HANDOFF.md`，至少更新：

- STEP status
- Implementation
- Validation
- Git commit
- Current stop point
- Known issues
- Security decisions
- Next step
- Roadmap

不要创建 `PROJECT_HANDOFF_V2.md`、`PROJECT_HANDOFF_V3.md` 或 `PROJECT_HANDOFF_FINAL2.md`。长期只维护 `PROJECT_HANDOFF.md`，历史由 Git 保存。

## 22. 状态词规范

只使用以下状态词：

- NOT STARTED
- IN PROGRESS
- PARTIALLY COMPLETED
- COMPLETED
- COMPLETED AND VERIFIED
- BLOCKED
- PLANNED
- OPTIONAL

避免使用“基本完成”“应该完成”“差不多完成”等模糊描述。

## 23. 关键文件索引

| 文件 | 作用 |
| --- | --- |
| `PROJECT_HANDOFF.md` | 跨聊天项目状态主索引 |
| `DATA_MAPPING.md` | Excel、JSON 与页面字段映射及图片规则 |
| `STEP4_FINAL_REPORT.md` | 网站 JSON 接入与端到端验收 |
| `STEP6_FINAL_REPORT.md` | 多人维护和生产安全最终报告 |
| `docs/data-schema.md` | JSON 数据结构定义 |
| `docs/production-architecture.md` | 多人维护生产架构、角色与并发控制 |
| `docs/operations.md` | 发布、异常、回滚和恢复操作 |
| `docs/deployment-options.md` | 托管平台比较与安全前提 |
| `README.md` | 项目日常维护入口 |
| `config.example.json` | 可提交的本地配置模板 |
| `.github/workflows/deploy.yml` | 可选 GitHub Pages 部署工作流 |

## 24. 本交接基线生成时的核对结论

- STEP 6 = COMPLETED AND VERIFIED
- STEP 7 = NOT STARTED
- GitHub Pages = NOT DEPLOYED
- Repository = Private
- Next Step = STEP 7 — 正式部署环境确定与上线
- 当前不得进入 STEP 7

