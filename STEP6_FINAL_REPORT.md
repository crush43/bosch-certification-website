# STEP 6 最终报告

完成日期：2026-09-14

## A. 当前推荐的生产架构图

```text
业务维护人员（多人）
        ↓
共享位置中的唯一正式 Data 目录
SharePoint / Teams / OneDrive 同步目录 / Bosch 网络共享盘
        ↓
指定同步电脑 + 指定发布人员
config.local.json → snapshot → 校验 → JSON / 图片
        ├── 可选 Archive
        ├── 本地 HTTP 预览
        └── Git commit / push
                         ↓
          Bosch IT / 信息安全批准的静态托管平台
```

业务 Excel、代码版本库和托管平台已经在流程上解耦。完整说明见 `docs/production-architecture.md`。

## B. 创建和修改文件

创建：

- `docs/production-architecture.md`
- `docs/deployment-options.md`
- `docs/operations.md`
- `scripts/record_publish.py`
- `tests/test_sync_safety.py`
- `STEP6_FINAL_REPORT.md`

修改：

- `scripts/excel_reader.py`
- `scripts/sync_excel.py`
- `sync_website.bat`
- `publish_website.bat`
- `config.example.json`
- `.gitignore`
- `README.md`
- `docs/data-schema.md`
- `data/meta.json`

网站 UI、ENTER1/2/3 业务结构和 `index.html` 未修改。

## C. config 外部 Excel 路径机制

`config.local.json` 支持：

```json
{
  "excelSource": "S:/CertificationWebsite/Data",
  "productionMode": true,
  "archiveSnapshots": true,
  "archiveDirectory": "S:/CertificationWebsite/Archive"
}
```

也支持 Windows UNC 路径。相对路径按项目目录解析。开发环境未配置时仍默认使用 `./excel`。生产模式拒绝从项目内 `./excel` 发布，避免把测试数据误当成正式数据。

## D. snapshot 机制

每次同步为三份源 Excel 创建独立的 `.build` 临时 snapshot。后续表格解析、图片提取和 JSON 生成只读取 snapshot，不持续读取共享源。

本机同步报告记录：

- 文件名
- 源路径
- 文件大小
- 源修改时间
- snapshot 时间
- SHA-256

网站使用的 `data/meta.json` 不包含源路径，避免发布包泄露内部共享盘结构。

## E. 文件变化检测机制

每份文件执行：

1. 复制前记录 size 和 mtime。
2. 复制到 snapshot。
3. 复制后再次检查 size 和 mtime。
4. 计算源文件和 snapshot 的 SHA-256。
5. 哈希后再次检查源文件 size 和 mtime。

任一状态变化或哈希不一致都会停止同步。单元测试通过 mock 在复制期间修改源文件，确认抛出 `Source changed while being copied`，不会进入正式数据替换。

## F. Excel 临时锁检测

同步前检查三份正式 Excel 对应的 `~$` 临时锁文件。检测到锁文件时返回失败并提示关闭、保存工作簿。

实际测试结果：

- 同步退出码：1
- 错误信息：`Excel lock file detected`
- `data/` 和 `assets/generated/` 哈希变化：0
- 测试锁文件：已删除

## G. 模拟共享盘测试结果

没有伪造 Bosch 真实共享盘。本轮使用独立本地模拟目录，并通过被 Git 忽略的 `config.local.json` 指向该目录。项目 `./excel` 没有参与生产模式读取。

测试过程：

1. 将三份测试 Excel 复制到模拟共享 Data 目录。
2. 在模拟 ENTER3 的第 7 行临时增加 `Shared Test` 和 `https://example.com`。
3. 运行 `sync_excel.py --production`。
4. 成功创建并验证 snapshot。
5. `reference_links.json` 从 3 条增加到 4 条。
6. 无界面真实浏览器加载本地网站，四个 JSON 均返回 HTTP 200。
7. ENTER3 页面成功显示 `Shared Test`，链接地址为 `https://example.com`。
8. 恢复模拟 Excel，SHA-256 恢复为原值 `AB461B6C29DA76CF0138F8C1AC43E50FB494A761B10658A7FD8FE5FEA8F75381`。
9. 再次同步后 ENTER3 恢复为 3 条。
10. 浏览器确认 `Shared Test` 已消失。
11. 模拟共享目录和本地配置已清理。

## H. 多人同时编辑风险处理

所有业务人员只维护共享位置中的唯一正式 Excel。snapshot、mtime/size 一致性、SHA-256 和锁文件共同防止读取保存过程中的半成品。SharePoint / OneDrive 第一阶段采用本地同步目录，不实现 Graph API 锁检查。

## I. 多人同时发布风险处理

第一阶段采用指定同步电脑或指定发布人员的单点发布方式，不实现分布式发布锁。发布脚本要求工作区开始时完全干净，并先执行 `git pull --rebase origin main`。拉取或 rebase 失败时停止，不自动覆盖远程修改。

## J. Git 发布流程

```text
检查 main / origin / 干净工作区
→ git pull --rebase origin main
→ 生产模式同步
→ 本地预览确认
→ 最终网站校验
→ 只暂存批准文件
→ git diff --cached --check
→ 人工确认 commit
→ 人工确认 push
→ fetch 验证 origin/main
→ 写发布历史
```

同步失败不会提交。push 失败明确报告 `LOCAL SYNC SUCCESS / PUBLISH FAILED`。托管平台部署必须单独确认。

## K. Archive 设计

`archiveSnapshots` 默认为 false。启用后，在成功完成 Excel 和业务校验后，将三份已验证 snapshot 与 `snapshot-manifest.json` 写入带时间戳的目录。先写临时目录，再原子重命名为正式归档目录。

模拟测试成功生成三个归档批次；最新批次包含三份 Excel 和 manifest。测试归档已随模拟目录清理。生产环境建议将 Archive 放在受控共享位置，并由 IT 确认保留周期和权限。

## L. Publish history 设计

Git push 成功并刷新 `origin/main` 后，`scripts/record_publish.py` 向 `logs/publish-history.jsonl` 追加一条 JSONL。记录包括发布时间、源文件元数据、记录数、图片统计、归档编号和 Git commit。

记录程序拒绝：

- 上次同步不是 success
- 上次同步不是 production
- 本地 HEAD 与 `origin/main` 不一致

模拟发布历史写入测试通过，测试文件已清理。日志不记录密码、Token 或 API 凭据。

## M. .gitignore 和敏感文件检查结果

已确认以下内容被忽略：

- `config.local.json` / `config.json`
- `.build/` / `temp_sync/`
- `logs/`
- `Archive/` / `Publish/`
- `*.xlsx` / `*.zip`
- `.env*` / `*.token` / `*.pem` / `*.pfx`
- Python 缓存

当前 Git 历史没有提交 Excel、ZIP、本地配置、日志、snapshot 或临时测试目录。

需要业务和信息安全注意：Private 仓库已经有网站运行所需的生成 JSON 和认证图片，其中 `reference_links.json` 包含 Bosch 内部链接。这是现有网站数据，不是本轮新增泄露。不得在未审查内容和未获得批准时公开仓库或启用公网网站。本轮没有删除历史，也没有更改仓库可见性。

## N. 托管方案比较

- GitHub Pages：与当前静态架构兼容度高、运维简单，但网站公开性和账户方案必须审查，只作为可选测试方案。
- Bosch 内部 Web Server：兼容度高，可使用内网访问控制，需 IT 配置服务器、权限、HTTPS 和发布路径。
- SharePoint / Microsoft 365：可用现有身份权限，但完整静态网站和脚本执行能力需实测，部署适配难度较高。
- 其他公司批准平台：只要支持 HTML、JSON 和图片即可复用当前生成结果。

最终生产平台需由 Bosch IT / 信息安全确认。详见 `docs/deployment-options.md`。

## O. README 多人维护说明

README 已增加：

- 唯一正式 Excel 原则
- 业务维护、发布、开发和 IT 角色
- TEST EXCEL 与 PRODUCTION EXCEL 区分
- snapshot 和锁文件保护
- 生产配置与可选归档
- 单点发布流程
- GitHub Pages 的可选测试定位

## P. operations.md 异常处理说明

`docs/operations.md` 已覆盖：

1. Excel 正在被编辑
2. 同步失败
3. Git push 失败
4. 网站数据错误
5. Git 与 Archive 两种回滚
6. 共享盘断开
7. 图片丢失
8. Excel 表头被修改
9. 两个人同时准备发布
10. 发布历史失败
11. 托管平台部署失败

## Q. 仍需 Bosch IT / 信息安全确认的问题

- 正式 Excel 的最终共享位置和权限组
- SharePoint / OneDrive 同步目录还是 Windows 网络共享盘
- 指定同步电脑和发布负责人
- Archive 的位置、访问权限、保留周期和备份策略
- GitHub Private 仓库是否允许保存当前生成 JSON、图片和内部链接
- GitHub Actions 是否允许使用
- 最终托管平台
- 网站是否允许公网访问
- 如果要求仅内部访问，应采用哪种身份认证和网络边界
- 内部服务器的 HTTPS、域名、日志和灾备要求
- 发布审批和审计记录的正式责任人

## R. STEP 7 建议

在 Bosch IT / 信息安全给出上述决定后，再进入 STEP 7。建议内容：

1. 接入真实批准的共享 Excel 目录。
2. 配置正式 `config.local.json`。
3. 建立发布人员和同步电脑操作清单。
4. 在批准的平台做非敏感试部署。
5. 验证访问控制、部署回滚和审计流程。
6. 再决定是否需要自动化 CI/CD 或集中式发布服务。

本轮不进入 STEP 7，不修改仓库 Public/Private 状态，不启用公网发布。
