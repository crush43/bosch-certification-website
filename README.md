# 博世认证网站维护说明

这是一个静态认证信息网站。认证工程师维护 Excel，脚本将 Excel 转换为网站使用的 JSON 和图片，再发布到经过 Bosch IT / 信息安全批准的静态托管平台。GitHub Pages 目前只是可选测试方案，不是默认生产结论。

```text
Excel → 数据同步与校验 → JSON/图片 → 本地预览 → Git提交 → 获批的静态托管平台
```

## 多人维护模式

正式环境只允许一套共享 Excel 作为唯一数据源。不要让多名员工各自保存一套“正式 Excel”再分别同步。

```text
业务维护人员共同编辑共享 Excel
→ 发布人员在指定同步电脑运行 snapshot、校验和预览
→ 发布人员确认后提交 Git
→ 获批平台部署网站
```

- 业务维护人员：只编辑共享 Excel，不需要安装 Python、Git，也不修改网站代码。
- 发布人员：使用指定同步电脑运行同步、预览和发布。
- 开发人员：维护同步程序、网站代码和文档。
- 系统管理员 / IT：管理 Git、托管平台、访问权限和恢复流程。

一个人可以兼任多个角色。第一阶段只允许一台指定同步电脑或一名指定发布人员执行正式推送。不要设置“Excel 保存后自动发布”，避免半成品直接上线。

## 首次安装

### 同步电脑

1. 安装 Python 3。
2. 获取完整项目文件夹。
3. 打开命令提示符或 PowerShell，进入项目目录。
4. 安装同步程序依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. 双击 `sync_website.bat` 测试同步。
6. 双击 `preview_website.bat`，浏览器打开 `http://localhost:8080` 后检查网站。

如果电脑使用 Python Launcher，也可以使用：

```powershell
py -3 -m pip install -r requirements.txt
```

### Git 管理员首次配置

管理员需要安装 Git，并将项目连接到已批准的 GitHub 仓库：

```powershell
git init -b main
git remote add origin <GitHub仓库地址>
```

首次提交前，请确认仓库的公开范围符合公司信息安全要求。网站 JSON 和图片会随 GitHub Pages 对访问者公开；不要把不允许公开的业务数据上传到公共仓库。

## 修改 Excel

开发测试数据默认位于 `excel/`：

- `ENTER 1-Basic Information.xlsx`
- `ENTER 20-Certification Mark.xlsx`
- `ENTER 3-Reference Link.xlsx`

修改规则：

- 保持现有 Sheet 名称不变。
- 保持现有表头名称和列顺序不变。
- 按现有格式增加或修改数据行。
- ENTER1、ENTER2 的图片放在对应记录和对应字段单元格中。
- ENTER3 的 A 列是标题，B 列是完整的 `http://` 或 `https://` 地址。
- 没有内容时留空，不要填写 `/`。
- 保存并关闭 Excel 后再同步，避免 Excel 锁文件阻止更新。

### TEST EXCEL 与 PRODUCTION EXCEL

- TEST EXCEL：开发环境可使用项目内的 `./excel`，不得替代正式业务数据。
- PRODUCTION EXCEL：必须位于批准的 SharePoint / Teams 文档库、OneDrive for Business 同步目录或 Bosch 网络共享盘。
- Git 仓库保存代码和已生成的网站版本，不把 Git 中的 Excel 当作正式多人维护入口。
- 不要把整个 Git 项目放在共享盘中供多人共同编辑。

## 同步数据

推荐双击：

```text
sync_website.bat
```

也可以在命令行运行：

```powershell
python scripts/sync_excel.py
```

同步成功时会显示：

```text
Validation: PASSED
JSON generated successfully.
Formal data replaced successfully.
```

同步程序会更新并校验：

- `data/basic_information.json`
- `data/certification_marks.json`
- `data/reference_links.json`
- `data/meta.json`
- `assets/generated/enter1/`
- `assets/generated/enter2/`

只有校验通过时才替换正式网站数据。同步失败不会覆盖上一次成功结果。

同步开始时，程序会先将三份 Excel 复制到本地 `.build` 快照目录，记录文件路径、大小、修改时间、快照时间和 SHA-256。后续解析只读取快照。复制前后发现文件发生变化、快照哈希不一致或检测到 `~$` 临时锁文件时，同步立即停止。

## 本地预览

双击：

```text
preview_website.bat
```

脚本会启动本地 HTTP 服务并打开：

```text
http://localhost:8080
```

预览时至少检查：

1. HOME 可以打开。
2. ENTER1 筛选、字段图片和图片放大正常。
3. ENTER2 搜索、筛选、展开和折叠正常。
4. ENTER3 链接标题和跳转地址正确。
5. 首页“最后更新”时间正确。

预览窗口按 `Ctrl+C` 可以停止服务。

不要直接双击 `index.html` 进行正式测试。浏览器的 `file://` 模式会阻止页面读取 JSON。

## 正式发布

### 推荐人工流程

1. 业务人员修改、保存并确认共享 Excel。
2. 发布人员确认 Git 工作区干净。
3. 执行 `git pull --rebase origin main`；出现冲突时停止。
4. 使用生产模式运行同步。
5. 完成本地预览。
6. 检查 Git 变更。
7. 提交批准的网站文件。
8. 推送到 `origin/main`。

生产模式命令：

```powershell
python scripts/sync_excel.py --production
```

生产模式拒绝使用项目内的 `./excel`，必须先配置外部共享数据源。

原有的简化人工流程仍可用于开发测试：

1. 修改并关闭测试 Excel。
2. 运行 `sync_website.bat`。
3. 确认显示 `Validation: PASSED`。
4. 运行 `preview_website.bat` 完成本地检查。

管理员命令示例：

```powershell
git status
git add index.html logo.png data assets .github README.md requirements.txt scripts tests docs DATA_MAPPING.md STEP4_FINAL_REPORT.md STEP6_FINAL_REPORT.md config.example.json .gitignore .gitattributes sync.bat sync_website.bat preview_website.bat publish_website.bat
git commit -m "Update certification website"
git push origin main
```

正式发布推荐运行 `publish_website.bat`。该脚本会：

- 要求开始时 Git 工作区干净。
- 执行 `git pull --rebase origin main`，冲突时停止。
- 使用 `--production` 从外部正式 Excel 创建快照并同步。
- 同步失败时立即停止，不执行 Git 操作。
- 要求用户确认已经完成本地预览。
- 只暂存批准的网站和维护文件。
- 创建提交前再次要求确认。
- 推送 `origin/main` 前最后确认。
- 只有远程推送成功后，才追加本机发布历史。

它不会无条件自动推送。

## 可选的 GitHub Pages 测试部署

项目包含：

```text
.github/workflows/deploy.yml
```

只有在 Bosch IT / 信息安全允许后，管理员才应在 GitHub 仓库中打开：

```text
Settings → Pages → Build and deployment → Source → GitHub Actions
```

推送到 `main` 后，GitHub Actions 会：

1. 检查必要静态文件是否存在。
2. 只组装网站运行需要的文件。
3. 上传 GitHub Pages artifact。
4. 部署到 `github-pages` 环境。

Pages artifact 只包含：

- `index.html`
- `logo.png`
- `data/`
- `assets/`
- `.nojekyll`

Excel、日志、快照、本地配置、Python 缓存和开发脚本不会进入 Pages artifact。

部署完成后，在 GitHub 的 `Actions` 页面打开最新的部署任务，可以看到实际 Pages URL。

## 同步失败怎么办

1. 不要继续提交或推送。
2. 查看窗口中的 `[ERROR]` 信息。
3. 确认三份 Excel 已保存并关闭。
4. 检查 Sheet 名称、表头、必填字段和 URL。
5. 修正 Excel 后重新运行 `sync_website.bat`。
6. 只有出现 `Validation: PASSED` 后才能发布。

失败日志会写入本机 `logs/`。该目录不会提交 GitHub。

## 如何回滚

### 首选方法：修复 Excel 后重新发布

如果错误来自 Excel：

1. 恢复 Excel 中的正确内容。
2. 重新运行同步。
3. 本地预览确认。
4. 创建新的修复提交并推送。

这种方式能够让 Excel 和网站继续保持一致。

### 管理员 Git 回滚

如果需要恢复上一 Git 版本，管理员应使用可追踪的 `git revert`，不要使用会丢失历史的强制重置：

```powershell
git log --oneline
git revert <错误提交ID>
git push origin main
```

推送回滚提交后，GitHub Pages 会自动重新部署上一版内容。

## 数据源与快照归档配置

没有本地配置时，同步器默认读取：

```text
./excel
```

仓库中的安全模板是：

```text
config.example.json
```

需要切换数据源时，在本机复制为 `config.local.json`：

```powershell
Copy-Item config.example.json config.local.json
```

本地目录示例：

```json
{
  "excelSource": "./excel",
  "productionMode": false,
  "archiveSnapshots": false,
  "archiveDirectory": ""
}
```

未来共享盘示例：

```json
{
  "excelSource": "S:/CertificationWebsite/Data",
  "productionMode": true,
  "archiveSnapshots": true,
  "archiveDirectory": "S:/CertificationWebsite/Archive"
}
```

UNC 路径示例：

```json
{
  "excelSource": "\\\\bosch-server\\department\\CertificationWebsite\\Data",
  "productionMode": true,
  "archiveSnapshots": true,
  "archiveDirectory": "\\\\bosch-server\\department\\CertificationWebsite\\Archive"
}
```

`config.local.json` 已被 `.gitignore` 忽略。不要把真实公司共享盘路径、用户名、密码、Token 或凭证写入可提交文件。

字段说明：

- `excelSource`：三份正式 Excel 所在目录。
- `productionMode`：设为 `true` 时启用正式数据源限制。
- `archiveSnapshots`：是否在成功校验时保存本次 Excel 快照。
- `archiveDirectory`：归档目录；启用归档但留空时，默认使用 Data 同级的 `Archive`。

发布成功记录保存在本机 `logs/publish-history.jsonl`。日志和归档不进入 Git。

## 未来共享盘部署

未来正式架构可以保持现有同步核心不变：

```text
博世共享盘或 SharePoint 同步目录
→ config.local.json 的 excelSource
→ 本地 snapshot
→ Excel 校验与同步
→ JSON和图片
→ 人工审核
→ GitHub或内部静态托管
```

当前阶段不包含 OneDrive API、SharePoint API、Microsoft Graph、Webhook、定时任务、数据库或多人权限系统。

完整架构见 `docs/production-architecture.md`，托管方案比较见 `docs/deployment-options.md`，生产异常处理见 `docs/operations.md`。最终生产平台需由 Bosch IT / 信息安全确认。

## 文件安全原则

可以提交：

- 网站 HTML、JSON 和生成图片
- GitHub Pages workflow
- 同步脚本和维护文档
- `config.example.json`

禁止提交：

- `.build/`
- `temp_sync/`
- `logs/`
- `config.local.json`
- `config.json`
- Python 缓存
- 密码、Token 和个人凭证
- 未经批准的公司内部路径或资料
