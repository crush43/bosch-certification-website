# STEP 9 最终报告

## A. 结论

完成日期：2026-09-14

状态：**COMPLETED AND VERIFIED (NON-PRODUCTION SHARED SOURCE)**

- 本轮规定的 17 项可执行 UAT / Failure / Recovery 测试全部通过。
- 正式网站数据基准保持不变：ENTER1 = 4、ENTER2 = 7、ENTER3 = 3、JSON 页面引用图片 = 39。
- GitHub Pages 在线网站已通过真实 Chrome 端到端测试。
- 本轮没有连接真实 Bosch Network Shared Drive。真实共享盘 UAT 必须在 STEP 8 获得真实 UNC 路径后补做。
- STEP 8 保持 `NOT STARTED — WAITING FOR REAL BOSCH NETWORK SHARED DRIVE PATH`；STEP 10 未开始。

## B. 测试环境与基线

| 项目 | 值 |
| --- | --- |
| 本地目录 | `E:\bosch` |
| 日期 / 时区 | 2026-09-14 / Asia/Shanghai |
| OS | Windows |
| 分支 | `main` |
| 测试起始 HEAD | `f2624f5d9c9b5d09fb1676caa5ec0720298388ff` |
| 测试起始 origin/main | 与 HEAD 一致 |
| Repository | `crush43/bosch-certification-website` / Public |
| Online URL | `https://crush43.github.io/bosch-certification-website/` |

除特别说明外，破坏性、异常和恢复测试均在 `temp_sync` 下的隔离副本、临时 Excel 或模拟 Git 环境执行。测试结束后临时目录已清理，不污染正式数据、Git 历史、发布日志或线上网站。

## C. 测试结果

### 1. 正常同步基线

- 目的：确认正常 Excel → JSON / 图片链路可用。
- 方法：在隔离项目中同步三份基准 Excel，并运行网站校验。
- 预期：同步和校验成功，数量为 4 / 7 / 3 / 39。
- 实际：完全符合预期。
- 结果：**PASS**。
- 清理：隔离产物随临时测试目录删除。

### 2. Excel 锁文件

- 目的：确认正在编辑的 Excel 不会被发布读取。
- 方法：在测试源创建规范的 `~$` 锁文件后同步。
- 预期：同步立即停止，正式 data / assets 不变。
- 实际：返回 `Excel lock file detected`；隔离正式输出哈希不变。
- 结果：**PASS**。
- 清理：锁文件已删除。

### 3. 必需 Excel 缺失

- 目的：确认三份源文件不完整时安全停止。
- 方法：临时移走 ENTER2 文件，运行同步后恢复。
- 预期：明确报缺失文件，不替换正式输出。
- 实际：明确报告 `ENTER 2-Certification Mark.xlsx` 缺失；输出不变。
- 结果：**PASS**。
- 清理：源文件已恢复。

### 4. 表头损坏

- 目的：确认必需列名被修改时拒绝生成。
- 方法：仅在测试 Excel 中将 ENTER2 的 `标志示意图` 改为错误表头。
- 预期：指出工作簿、Sheet 和缺失表头，输出不变。
- 实际：错误定位完整，正式隔离输出未替换。
- 结果：**PASS**。
- 清理：测试工作簿随临时目录删除。

### 5. URL 非法与必填值缺失

- 目的：验证业务字段校验。
- 方法：分别把 ENTER3 URL 改为 `not-a-valid-url`、把名称置空。
- 预期：两种输入均被拒绝，不覆盖旧数据。
- 实际：分别报告 URL 必须以 HTTP/HTTPS 开头、名称必填；输出哈希不变。
- 结果：**PASS**。
- 清理：测试工作簿随临时目录删除。

### 6. Snapshot 期间源文件变化

- 目的：防止复制过程中读取不一致内容。
- 方法：执行 `SnapshotSafetyTests.test_source_change_during_snapshot_is_rejected`。
- 预期：检测变化并停止。
- 实际：单元测试通过。
- 结果：**PASS**。
- 清理：测试夹具自动清理。

### 7. 生成 JSON / 图片损坏

- 目的：确认发布前校验能拦截坏 JSON 和缺图。
- 方法：在隔离副本中分别破坏 `meta.json`、移走一个已引用图片。
- 预期：校验失败并给出明确原因。
- 实际：分别返回 JSON 解析错误和缺失图片路径；图片随后恢复。
- 结果：**PASS**。
- 清理：隔离改动已删除。

### 8. Git 工作区不干净

- 目的：禁止混入未经批准的文件。
- 方法：在正式项目创建临时探针文件后启动发布。
- 预期：提交前立即阻止。
- 实际：显示 `[BLOCKED] The Git working folder already contains changes.`。
- 结果：**PASS**。
- 清理：探针已删除，工作区恢复干净。

### 9. 非 main 分支发布

- 目的：确认生产发布仅允许 `main`。
- 方法：建立临时测试分支后启动发布。
- 预期：发布被阻止。
- 实际：明确报告当前分支不是 main。
- 结果：**PASS**。
- 清理：已切回 main 并删除临时分支。

### 10. Remote / pull 失败

- 目的：确认无法同步远端时不会继续生成或发布。
- 方法：短暂将本地 origin 指向不可达测试地址，在 finally 中恢复。
- 预期：pull/rebase 失败后停止。
- 实际：显示 `[BLOCKED] Git pull/rebase failed`，未执行同步和发布。
- 结果：**PASS**。
- 清理：origin 已恢复为正式 GitHub 地址。

### 11. Push 失败

- 目的：区分“本地同步成功”和“线上发布成功”。
- 方法：在完全隔离的发布脚本环境模拟 push 返回失败。
- 预期：保留本地提交、线上仍是旧版本、不写成功发布历史。
- 实际：显示 `LOCAL SYNC SUCCESS / PUBLISH FAILED`，历史记录函数未调用。
- 结果：**PASS**。
- 清理：模拟环境已删除。

### 12. GitHub Pages 部署失败与恢复

- 目的：验证代码推送成功但平台部署失败的识别和恢复。
- 方法：核对真实历史失败 run `34794190681`、后续成功 run `34796402982` 和当前在线 URL。
- 预期：失败原因可定位，Git 历史不丢失；恢复后 Pages 正常。
- 实际：失败 run 的 build 为 failure、deploy 为 skipped，失败步骤为 `Configure GitHub Pages`；后续 run 为 success，SHA 为 `f2624f5...`；当前首页 HTTP 200。
- 结果：**PASS**。
- 清理：只读检查，无需清理。

### 13. Git revert 回滚

- 目的：验证不改写历史的上一版本恢复方法。
- 方法：在隔离 Git 仓库提交错误版本，再执行 `git revert`。
- 预期：产生新的回滚提交，仓库内容恢复到已知良好版本。
- 实际：历史保留“良好 → 错误 → revert”三次提交；Git 内容差异为零；网站校验通过。
- 结果：**PASS**。
- 清理：隔离仓库已删除。

### 14. Archive 创建、完整性与恢复

- 目的：验证归档可用于业务源恢复。
- 方法：使用本地隔离“生产模式”创建 Archive，校验 manifest 与三份 Excel 哈希，再从归档副本同步。
- 预期：manifest 完整、哈希一致、恢复同步通过。
- 实际：三份 Excel 全部存在且 SHA-256 与 manifest 一致；恢复后 4 / 7 / 3 / 39 校验通过。
- 结果：**PASS（模拟 Archive，不是 Bosch 正式归档）**。
- 清理：归档测试目录已删除。

### 15. 发布历史写入条件

- 目的：只在“生产同步成功、远端一致”时写成功历史。
- 方法：依次测试同步失败、非生产模式、HEAD 与 origin/main 不一致、完全成功四种报告。
- 预期：前三种拒绝，最后一种只写一条且不泄露 sourcePath。
- 实际：完全符合预期；成功测试记录 commit 为 `f2624f5...`，不含源路径。
- 结果：**PASS**。
- 清理：测试历史文件已删除。

### 16. 共享数据源不可达

- 目的：确认外部源不可用时不回退到本地测试 Excel。
- 方法：让隔离生产配置指向不存在的外部目录。
- 预期：同步停止，旧输出保持不变。
- 实际：必需 Excel 不可用错误明确，data / assets 哈希不变。
- 结果：**PASS（本地不可达路径模拟）**。
- 清理：测试配置随临时目录删除。

### 17. 线上浏览器 UAT

- 目的：确认最终用户页面的真实加载、查询与异常提示。
- 方法：使用本机 Chrome 访问正式 Pages URL，并安全拦截一次 JSON 请求测试错误态。
- 预期：首页、三个模块、筛选、搜索、图片、链接、多语言、移动端及错误提示正常。
- 实际：
  - 正常加载约 1.8 秒达到 ready；首页 3 个入口。
  - ENTER1 显示 4 条；选择“中国”后为 1 条，摘要正确。
  - ENTER2 显示 7 条；搜索 `161111B006` 精确得到 UL 1 条。
  - ENTER3 显示 3 张卡、3 个 HTTPS 链接，均使用新窗口与 `noopener noreferrer`。
  - 页面生成图片元素 43 个（同一来源可在不同卡片位置重复展示），broken image = 0；JSON 唯一引用图片仍为 39。
  - 英文切换正常；390px 视口无横向溢出。
  - 正常场景 console error = 0、failed request = 0。
  - 受控阻断 `basic_information.json` 后，应用进入失败态并显示“数据加载失败，请刷新页面或联系认证工程师”。
- 结果：**PASS**。
- 清理：关闭无界面浏览器，未修改线上状态。

## D. 完整性与安全结论

- 正式 `data/`、`assets/` 与 `origin/main` 无差异。
- 测试期间没有把测试 Excel、测试配置、Archive、日志或临时文件加入 Git。
- 正式 origin URL、main 分支和工作区均已恢复。
- 所有失败场景均证明：失败不会静默覆盖上一版正式网站数据。

## E. Pages 与恢复结论

- 历史平台失败有明确证据，失败步骤可定位。
- 后续成功 workflow 与测试起始 HEAD 一致。
- 当前线上首页为 HTTP 200，完整浏览器 UAT 通过。
- `docs/operations.md` 已补充 Pages 部署失败的明确处理和恢复步骤。

## F. 限制与后续补测

以下内容本轮未执行，不能被描述为已经验证：

- 真实 Bosch UNC 路径的连通性、权限、断连、延迟和并发编辑。
- 指定生产发布电脑与正式发布责任人的现场操作。
- 正式 Archive 位置、权限、保留周期与恢复演练。

因此本轮结论限定为 `NON-PRODUCTION SHARED SOURCE`。获得真实 Bosch Network Shared Drive UNC 路径后，应先完成 STEP 8，再补做真实共享源 UAT。

## G. Final Result

```text
STEP 9:
COMPLETED AND VERIFIED (NON-PRODUCTION SHARED SOURCE)

Executable tests:
17 / 17 PASS

GitHub Pages:
DEPLOYED AND VERIFIED

STEP 8:
NOT STARTED — WAITING FOR REAL BOSCH NETWORK SHARED DRIVE PATH

STEP 10:
NOT STARTED
```
