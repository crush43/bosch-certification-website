# 生产运维与异常处理

## 角色和唯一数据源

- 业务维护人员：只编辑共享位置中的唯一一套正式 Excel，不需要 Python、Git 或网站代码权限。
- 发布人员：在指定同步电脑上执行同步、预览、确认和发布。
- 系统管理员 / IT：管理 Git 仓库、托管平台、访问权限和故障恢复。

一个人可以兼任多个角色。第一阶段只允许一台指定同步电脑或一个指定发布人员执行正式推送，不开发账号系统。

## 标准发布流程

```text
多人编辑同一套共享 Excel
→ 保存并完成业务确认
→ 发布人员运行生产同步
→ 创建本地 snapshot
→ 校验并生成 JSON/图片
→ 本地预览
→ 人工确认
→ Git commit / push
→ 在批准的托管平台检查部署
```

不要把“保存 Excel”与“自动发布网站”绑定。共享 Excel 是业务数据源，Git 是代码和发布版本记录，托管平台负责提供网站。

## Excel 正在被其他人编辑

1. 请对方保存并关闭 Excel。
2. 确认目录中没有对应的 `~$` 临时锁文件。
3. 等待 OneDrive / SharePoint 同步完成，或确认共享盘文件状态稳定。
4. 重新运行同步。

检测到锁文件或复制期间文件的大小、修改时间发生变化时，同步会停止，正式数据不会被替换。

## 同步失败

1. 不要继续预览确认、提交或推送。
2. 查看窗口错误和 `logs/sync-report.json`。
3. 检查三份文件是否齐全、可读并已关闭。
4. 检查 Sheet 名称、表头、必填字段、URL 和图片锚点。
5. 修复共享 Excel 后重新同步。

只有显示 `Validation: PASSED` 才能进入预览。数据生成失败时，网站继续使用上一版正式数据。

## Git push 失败

此时状态是：

```text
LOCAL SYNC SUCCESS
PUBLISH FAILED
```

本地生成数据和提交可以存在，但线上仍是旧版本。不要把本地同步成功描述为发布成功。检查网络、Git 凭据和远程分支；确认没有其他人发布后，再重新推送。

## 网站数据错误

1. 立即停止新的发布。
2. 记录错误页面、数据项和当前 Git commit。
3. 优先使用 `git revert <错误提交ID>` 创建可追踪回滚提交并推送。
4. 修复正式 Excel，重新同步、预览和发布。
5. 如需调查历史业务数据，可读取 Archive 中与发布记录对应的快照。

## 回退上一版本

首选网站恢复：

```text
git log --oneline
git revert <错误提交ID>
git push origin main
```

不要使用会抹去历史的强制重置。

业务数据恢复可以从 Archive 选取历史 Excel，复制回正式 Data 前必须经过业务负责人确认，然后重新同步和发布。

## 共享盘断开

1. 不要把本地旧副本临时冒充正式数据源。
2. 恢复网络或 OneDrive 同步。
3. 确认 `config.local.json` 的路径可访问。
4. 核对三份文件的修改时间后重新同步。

## 某张图片丢失

1. 在正式 Excel 对应记录和字段中重新嵌入正确图片。
2. 不要直接向 `assets/generated` 手工补图。
3. 重新同步，确认图片数量和预览结果。

## Excel 表头被修改

同步会报告缺失的必需表头并停止。根据 `docs/data-schema.md` 恢复原表头，不要通过修改同步代码来迁就未经批准的临时列名。

## 两个人同时准备发布

第一阶段由指定发布人员协调，只允许一个发布过程。后开始的人必须等待。发布前脚本会要求工作区干净并执行 `git pull --rebase origin main`；出现远程变化或冲突时停止，不自动覆盖。

## 发布记录

生产推送成功后，脚本向本机 `logs/publish-history.jsonl` 追加一条记录。记录包含时间、源文件哈希、记录数、图片统计、归档编号和 Git commit，不包含密码、Token 或账号凭据。

如果推送成功但历史记录失败，脚本会明确显示：

```text
PUBLISH SUCCESS / HISTORY RECORD FAILED
```

此时不要重复发布同一内容；由管理员补查记录。

## 托管平台故障

Git push 成功不等于网站部署成功。发布人员还必须检查获批托管平台的部署结果和实际页面。托管失败时，Git 中的发布版本仍可追踪，但应标记为“代码已推送，部署失败”。

### GitHub Pages 部署失败恢复

1. 打开仓库 Actions，找到与刚推送 commit 对应的 `Deploy certification website to GitHub Pages` run。
2. 记录失败 run ID、commit SHA、失败 job 和失败 step；不要把 Git push 成功误记为网站发布成功。
3. 保留 Git 历史和本地提交，不使用强制 push，不删除当前仍可用的上一版 Pages。
4. 若失败发生在 `Configure GitHub Pages`，由仓库管理员确认 Pages Source 为 GitHub Actions、Pages 已启用、workflow 权限可用。
5. 若失败发生在网站校验或构建，先在本地修复 Excel / JSON / 图片并通过 `scripts/validate_site.py`，再提交修复版本。
6. 修复后重新运行失败 workflow 或推送修复提交，等待 build 与 deploy 均显示 success。
7. 访问正式 URL，确认首页、三个 JSON、图片、ENTER1/2/3 和浏览器控制台正常，再把状态更新为发布成功。

在平台恢复前，线上继续使用上一版成功部署内容。若错误版本已经上线，按“回退上一版本”使用 `git revert` 创建可追踪恢复提交。
