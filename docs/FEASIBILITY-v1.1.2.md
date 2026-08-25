# v1.1.2 可行性报告

> 2026-08-25 · mihomo-core-fnos

## 需求清单

| # | 需求 | 结论 |
|---|---|---|
| 1 | 订阅默认值改为打开局域网访问（allow-lan: true） | ✅ 可行 |
| 2 | 内核热更新：点击状态页版本号即可更新（当前内核 v1.19.29） | ✅ 可行 |

---

## 需求 1：订阅更新强制 allow-lan: true

### 现状问题

`app/status_server.py::_update_subscription()` 与 `cmd/main::apply_subscription()`
拉取订阅后只强制改写 `mixed-port` / `port` / `socks-port` / `external-controller`，
**不处理 `allow-lan`**。订阅源返回 `allow-lan: false` 时，每次更新订阅后局域网
设备（手机/其他机器走 7890）全部断连，需手动改回。

实测（2026-08-25，31.101）：运行配置 `config.yaml:7 allow-lan: true` 为手动修复值；
Miaogic 订阅原始内容为 `false`，每次"手动获取订阅"都会覆盖回 false。

### 方案

与现有端口强制改写同模式，两处各加正则替换 + 缺行追加：

```python
data = _re.sub(r"(?m)^allow-lan:.*$", "allow-lan: true", data)
if not _re.search(r"(?m)^allow-lan:", data):
    data = data.replace("mixed-port: 7890", "mixed-port: 7890\nallow-lan: true", 1)
```

改动点：
- `app/status_server.py` `_update_subscription()` — 状态页手动获取订阅路径
- `cmd/main` `apply_subscription()` — 启动时自动应用订阅路径

## 需求 2：内核热更新（点击版本号）

### 实测验证链路（2026-08-25 全部通过）

| 环节 | 结果 |
|---|---|
| GitHub latest API (`MetaCubeX/mihomo`) | 最新 v1.19.30（内置打包版 v1.19.29） |
| 下载 `mihomo-linux-amd64-v1.19.30.gz`（18MB，走本机代理） | ✅ ~10s |
| gunzip 后 `-v` 版本验证 | ✅ 正常执行 |
| mihomo-core 用户对 `/vol4/@appcenter/mihomo-core/` 写权限 | ✅ 实测可写 |
| 运行中 ELF 原子替换 | ✅ Linux rename 安全（旧 inode 由运行中进程持有） |
| 磁盘空间（vol4） | ✅ 剩余 750G |

### 交互设计

状态页「内核版本」行显示 `v1.19.29`（可点击），点击后：

```
GET /api/update_core
  → 1. GitHub API 查 latest 版本号
  → 2. 与当前内核版本比对，相同则返回 "已是最新"
  → 3. 下载 .gz 到 DATA_DIR/mihomo.new.gz（约 18MB）
  → 4. 解压 → chmod +x → ./mihomo.new -v 校验版本一致
  → 5. mv 原子替换 app 目录的 mihomo 二进制
  → 6. 调 cmd/main restart（stop → start，代理中断 3~5 秒）
  → 7. 返回新版本号；前端刷新状态
```

### 风险与对策

| 风险 | 对策 |
|---|---|
| 更新期间代理中断 3~5 秒 | 状态页不依赖代理，触发不受影响；前端提示"重启中" |
| 下载 GitHub 需代理，而代理就是 mihomo 自身 | NAS 上 GeoIP 判定 GitHub 走代理，正常成立；下载失败即中止并保留旧内核（先下到临时文件，校验通过才替换） |
| fnOS 升级 fpk 会用打包内二进制覆盖 app/mihomo | 属预期行为：升级后回到打包时版本。热更新的意义在于两次发版之间快速跟进上游内核 |
| 半途断电/下载损坏 | 临时文件 + `-v` 校验通过才替换，任何失败不动原内核 |

### 不做的事

- 不做自动定时更新（用户明确要手动点击触发）
- 不做多架构下载（本应用 manifest 锁 x86_64）

---

## 打包信息

- **版本**：1.1.1 → **1.1.2**（101 上已是 1.1.1，递增合理）
- 三处版本号同步：`manifest` / `app/status_server.py APP_VERSION` / `cmd/main`
- CHANGELOG 补 [1.1.2] 条目
- 构建产物交付 `fpk/mihomo-core/`，旧包迁 `old_fpk/`
