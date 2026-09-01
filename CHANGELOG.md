# Changelog

## [1.1.5] - 2026-09-02

- **面板版本显示 + 一键更新**：状态页「内核状态」新增「面板版本」行（紧跟内核版本下方），显示 MetaCubeXD 面板版本（读面板 `/__version`）；点击版本号无感触发面板更新（调面板 `POST /upgrade`，面板自身下载上游 gh-pages 替换 www 并保留 config.js，不中断代理）。配合 metacubexd-fnos 的面板更新接口使用
- 新增端点：`GET /api/panel_version`（读面板版本）、`POST /api/update_panel`（触发面板更新）

## [1.1.4] - 2026-09-02

- **自定义规则独立落库**：新增独立文件 `custom-rules.txt`（DATA_DIR），用户自定义规则（AI 域名、中转站等）存于此，订阅更新**不再覆盖**。订阅刷新后通过 `type: file` rule-provider 重新注入 config.yaml（`RULE-SET,custom` + `rule-providers.custom`）。状态页手动获取（`_update_subscription`）与启动自动应用（`apply_subscription`）两条路径均已覆盖
- **局域网规则 API**：新增 `GET /api/custom_rules`（查看）与 `POST /api/custom_rules`（添加，body `{"rule":"example.ai"}`，自动规范化并热重载），供 agent / 脚本快速添加自定义规则

## [1.1.2] - 2026-08-25

- **订阅更新强制 allow-lan: true**：订阅源返回 `allow-lan: false` 时自动改写为 `true`（缺行则追加），修复每次更新订阅后局域网设备断连问题。状态页手动获取（`_update_subscription`）与启动自动应用（`apply_subscription`）两条路径均已覆盖
- **内核热更新**：状态页品牌行新增「内核 v1.19.x」可点击文字，点击确认后自动 GitHub 查 latest → 下载 → 解压校验 → 原子替换二进制 → 重启内核进程，无需重新打包发版。任何一步失败均保留原内核
- 新增 `/api/update_core` 端点；详见 `docs/FEASIBILITY-v1.1.2.md` 可行性报告

## [1.1.1] - 2026-08-18

- 状态页订阅状态文案优化（简化显示，保留手动更新功能）
- 状态页容器加宽到 1200px + 内容垂直居中

## [1.1.0] - 2026-08-18

- **合并上游 mihomo Meta v1.19.30**（从 v1.19.29 升级）
- **修复启动脚本 cmd/main 关键 bug**：
  - 修复端口被占用时 `start()` 提前返回导致 status page 不启动（fnOS 报 `status_page=no`）
  - 移除 `set -e`（errexit），避免 curl/pkill 失败导致脚本提前退出
  - `status()` 增加端口探测 fallback，PID 文件丢失时仍能正确检测
  - `start_status()` 增加端口占用检测，避免重复启动
  - `stop()` / `stop_status()` 中 pkill 统一加 `|| true`
- **订阅状态文字改为可点击手动获取**（去掉独立按钮）
- **状态色逻辑**：未配置=灰 / 有节点=绿(显示节点数) / 无节点=灰(可点击重试)
- **首次配置自动获取**

## [1.0.6] - 2026-08-17

- **状态页新增「手动获取订阅」按钮**：点按钮触发订阅拉取（clash.meta UA → 完整 YAML）→ 写 config.yaml → Clash API 热重载，无需重启进程；显示拉取节点数
- **前端版本号对齐**：status_server.py / cmd/main 的 APP_VERSION 默认值对齐到 1.0.6，修复版本号落后 1 的问题
- 内置 mihomo Meta v1.19.29 (x86_64) + geoip 预置

## [1.0.5] - 2026-08-13

- **修复品牌 logo 截取**：状态页居中基础上向上偏移由 `-10%` 调为 `-5%`（移动端 `-8%`→`-3%`），logo 完整显示

## [1.0.4] - 2026-08-13

- **状态页垂直居中 + 向上偏移 10%**（桌面），移动端适配（@media 600px）
- **文案调整**：MetaCubeXD 引导两行排版定稿，去掉多余句号
- **移动端适配**：缩小 padding/字号，避免说明文字被挤成 3 排
- **修复 % 转义**：CSS `translateY(-10%)` 的 `%` 与 `PAGE % dict` 格式化冲突导致状态页崩溃，改为 `%%`
- **修复 cmd/main target 路径 bug**：mihomo/状态页实际在 `${APP_DIR}/target/`，兼容 TRIM_APPDEST 各种取值
- 仅保留 iframe 版本

## [1.0.3] - 2026-08-11

- **应用设置配置订阅**：App Center 设置里填订阅链接，自动配置进 mihomo 内核（proxy-providers）
- **状态页订阅状态**：显示订阅 provider 名称 + 节点数
- 状态页文案定稿：两行排版，引导区分未装/已装 MetaCubeXD 面板
- API 地址动态获取 NAS IP，**点击复制**（带"已复制 ✓"提示）
- 状态页显示应用版本号（v1.0.3）
- 双版本打包：url 版 + iframe 版
- 卸载时彻底清理进程并释放端口（修复重装端口占用）

## [1.0.2] - 2026-08-11

- 状态页显示**应用版本号**（v1.0.2）
- 双版本打包：url 版 + iframe 版
- 卸载时彻底清理进程并释放端口（修复重装端口占用）

## [1.0.1] - 2026-08-11

- 新增自带**状态页**（:9092，桌面入口），显示内核在线/版本/节点数/规则数
- 状态页提示的 Clash API 地址改为动态获取 **NAS 局域网 IP**（修复 `127.0.0.1` 无法跨设备访问的问题）
- 遵循 **GPLv3**（mihomo 内核许可证）合规：附带 GPL-3.0.txt，安装时显示协议同意

## [1.0.0] - 2026-08-11

- 独立 mihomo 内核代理服务（自启）
- mixed 代理 `7890` + Clash API `9090`
- geoip.metadb 预置（避免内核首次启动从公网下载失败）
- 配合 MetaCubeXD 面板控制节点
