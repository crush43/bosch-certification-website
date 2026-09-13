# 部署平台选择

认证网站由静态 HTML、JSON 和图片组成。Excel 数据层、同步器、生成文件和托管平台保持解耦。更换托管平台时，不应重写 Excel 解析和网站数据结构。

最终生产平台需由 Bosch IT / 信息安全确认。本文件只比较技术适配性，不代表任何 Bosch 内部政策或批准结论。

## 共同安全前提

- 先确认网站内容是否允许对公网公开。
- Git 仓库私有不等于网站访问也是私有。
- 正式 Excel、共享盘路径、日志、快照和凭证不得进入公开部署包。
- 发布包只需要 `index.html`、`logo.png`、`data/`、`assets/` 和 `.nojekyll`。
- 发布人员必须先完成同步、校验和人工预览。

## 方案比较

| 方案 | 静态文件支持 | 公网要求 | 访问控制 | 部署难度 | 运维难度 | 当前架构兼容度 |
| --- | --- | --- | --- | --- | --- | --- |
| GitHub Pages | 原生支持 HTML、JSON、图片 | 通常面向公网；私有仓库也不能自动保证网站私有 | 普通项目站点的访问控制有限，具体能力取决于账户和企业配置 | 低 | 低 | 高，仓库已有可选 Actions 工作流 |
| Bosch 内部 Web Server | 通常支持，需确认服务器配置和 MIME 类型 | 不需要，可部署在内网 | 可接入公司现有网络和身份控制，需 IT 配置 | 中 | 中 | 高，只需复制精简发布包 |
| SharePoint / Microsoft 365 静态资源方式 | 可保存文件，但直接托管完整静态站点的能力和脚本策略需验证 | 通常不需要公网 | 可使用 Microsoft 365 权限，具体限制需 IT 确认 | 中到高 | 中 | 中，可能需要调整页面托管方式，但 Excel 同步器不变 |
| 其他公司批准平台 | 取决于平台 | 取决于平台 | 取决于平台 | 待评估 | 待评估 | 只要支持静态文件，通常较高 |

## 当前建议

1. 正式 Excel 优先存放在 Teams 背后的 SharePoint 文档库、OneDrive for Business 同步目录或 Bosch 网络共享盘。
2. 指定一台同步电脑和一名发布负责人。
3. 同步电脑通过 `config.local.json` 指向共享 Excel。
4. 发布人员运行生产同步、预览并确认。
5. 将生成文件提交到 Private Git 仓库。
6. 由 Bosch IT / 信息安全选择并批准最终托管平台。

GitHub Pages 当前只作为可选测试发布方案，不是默认生产结论。仓库保持 Private，程序不会自动修改仓库可见性或启用公网发布。

## SharePoint / OneDrive 预留方式

优先采用本地同步目录：

```text
SharePoint / Teams 文档库
→ OneDrive 同步到指定 Windows 目录
→ config.local.json 的 excelSource
→ 本地 snapshot
→ Excel 校验与网站生成
```

此方式不需要 Microsoft Graph、OAuth 或 Token。只有本地同步目录无法满足要求时，才评估 API 集成。
