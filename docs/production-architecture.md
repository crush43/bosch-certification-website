# 多人维护生产架构

## 推荐架构

```text
业务维护人员（多人）
        │
        ▼
SharePoint / Teams / OneDrive 同步目录 / Bosch 网络共享盘
唯一正式 Data 目录（三份 Excel）
        │
        ▼
指定同步电脑 + 指定发布人员
config.local.json → 本地临时 snapshot → 校验 → JSON / 图片
        │
        ├── 可选 Archive：保存已验证 Excel 快照和 manifest
        ├── 本地 HTTP 预览：业务确认
        └── Git commit / push：代码和发布文件版本记录
                         │
                         ▼
          Bosch IT / 信息安全批准的静态托管平台
```

共享位置只保存正式业务 Excel 和可选归档，不承担代码版本管理。Git 仓库保存同步程序、网站代码和生成后的发布文件，不作为多人编辑正式 Excel 的入口。

## 推荐共享目录

```text
CertificationWebsite/
├── Data/
│   ├── ENTER 1-Basic Information.xlsx
│   ├── ENTER 2-Certification Mark.xlsx
│   └── ENTER 3-Reference Link.xlsx
├── Archive/
├── Publish/
└── Documentation/
```

- `Data`：唯一正式 Excel。
- `Archive`：成功校验后的可选快照。
- `Publish`：内部服务器需要直接接收静态发布包时使用；当前同步器不自动写入。
- `Documentation`：面向业务维护人员的操作说明。

## 状态定义

- Draft：共享 Excel 正在编辑或尚未经过发布人员检查。
- Validated：snapshot 已建立，Excel、JSON 和图片校验通过，但尚未成功推送或部署。
- Published：Git push 成功并写入 `logs/publish-history.jsonl`。托管平台部署结果仍需单独检查。

“本地同步成功”和“正式发布成功”必须分开报告。Git push 或托管部署失败时，线上继续使用上一版。

## 并发控制

### 多人编辑

所有业务人员维护同一套共享 Excel。同步器复制前后检查大小和修改时间，再核对 SHA-256；发现变化或 `~$` 锁文件时停止。解析过程只读取 snapshot。

### 多人发布

第一阶段不实现分布式锁。通过指定同步电脑或指定发布人员实现单点发布。发布脚本要求 Git 工作区干净，先执行 `git pull --rebase origin main`；冲突时停止并保留人工处理。

## 权限边界

- 业务人员只需要共享 Data 目录编辑权限。
- 发布人员需要读取 Data、写入可选 Archive、运行同步程序和推送 Git 的权限。
- IT 管理 Git 仓库、托管平台和访问控制。
- `config.local.json` 不保存用户名、密码、Token 或 OAuth 信息。

最终共享目录、权限组、保留周期、备份策略和托管平台必须由 Bosch IT / 信息安全确认。
