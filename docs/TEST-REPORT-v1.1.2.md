# v1.1.2 完整测试报告

> 测试时间：2026-08-25 11:50–11:58 · 环境：FN-NAS 31.101（fnOS，x86_64）· 生产实例 mihomo-core

## 测试结论：全部通过 ✅

| # | 测试项 | 结果 |
|---|---|---|
| 1 | 状态页 UI 元素 | ✅ 5/5 |
| 2 | /api/status 数据完整性 | ✅ 8/8 |
| 3 | allow-lan 强制改写 | ✅ 4/4 |
| 4 | 内核热更新（uptodate 路径） | ✅ |
| 5 | fpk 包完整性 | ✅ |
| 6 | 局域网代理连通性 | ✅ HTTP 200, 0.21s |
| 7 | 状态页局域网可达 | ✅ HTTP 200 |

---

## 1. 状态页 UI 元素

| 检查项 | 结果 |
|---|---|
| `updateCore()` 入口存在 | ✅ |
| 「内核版本」行可点击（cursor:pointer + onclick） | ✅ |
| 无 alert 弹窗（结果就地显示） | ✅ |
| 顶部品牌行无重复文案 | ✅ |
| confirm 防误触确认保留 | ✅ |

## 2. /api/status 数据完整性

```
✅ ok = true（Clash API 在线）
✅ app_version = 1.1.2
✅ version = v1.19.30（经热更新升级）
✅ mode = rule
✅ proxies = 196
✅ rules = 51
✅ subscription_configured = true（Miaogic）
✅ sub_proxies = 161
```

## 3. 订阅更新强制 allow-lan: true

| 用例 | 输入 | 预期 | 结果 |
|---|---|---|---|
| case1 | `allow-lan: false` | 改写为 true | ✅ |
| case2 | 无 allow-lan 行 | 追加 `allow-lan: true` | ✅ |
| case3 | `allow-lan: true` | 保持不变 | ✅ |
| 生产配置 | 实际 config.yaml | allow-lan: true | ✅ |

覆盖路径：状态页手动获取订阅（`_update_subscription`）+ 启动自动应用（cmd/main `apply_subscription`）两处逻辑一致。

## 4. 内核热更新

### 真实升级链路（用户实测）

- 点击「内核版本」→ confirm 确认 → GitHub latest 查询 → 下载 v1.19.30（18MB）→ 解压校验 → 原子替换 → 重启内核进程
- 第一次尝试下载中断报"Remote end closed connection without response"，**原内核未受影响**（安全设计生效）
- 第二次重试成功：`v1.19.29 → v1.19.30`，内核进程重启加载新版本
- 升级后 Clash API `/version` 确认为 `v1.19.30`

### uptodate 幂等路径

```
GET /api/update_core → {"ok": true, "uptodate": true, "message": "已是最新版本 v1.19.30"}
```

### 已知问题（本版修复）

- ~~alert 弹窗体感差~~ → 结果就地显示在版本号行 3 秒（97105e0）
- ~~版本号 vv 重复~~ → 去除前端重复拼接（291463e）
- ~~confirm 文案换行致 JS 语法错误~~ → 单行文案（8bcd272）

### GitHub 下载稳定性备注

直连 github.com 偶发连接中断（GFW 干扰）。下载失败时临时文件清理、原内核保留，
重试即可。后续版本可考虑增加失败自动重试（2 次）。

## 5. fpk 包完整性

| 检查项 | 结果 |
|---|---|
| manifest version = 1.1.2 | ✅ |
| 包内 status_server.py 含热更新功能 | ✅ |
| 包内无 alert 弹窗代码 | ✅ |
| 包内 allow-lan 强制逻辑（2 处路径） | ✅ |
| wizard/config 在包内 | ✅ |
| 打包内核二进制 v1.19.29（可经热更新升 v1.19.30） | ✅ 符合设计 |

双版本产物：
- `mihomo-core-1.1.2.fpk`（url 版）
- `mihomo-core-1.1.2-iframe.fpk`（iframe 版）

交付位置：`/vol1/1000/fnOS App/fpk/mihomo-core/`；旧版已迁 `old_fpk/mihomo-core/`。

## 6. 局域网代理连通性

从局域网另一台机器（31.31）走 `192.168.31.101:7890` 代理访问外网：

```
HTTP 200, 0.212s ✅
```

验证了 allow-lan: true 生效、mixed 端口正常工作。

## 7. 状态页局域网可达

`http://192.168.31.101:9092/api/status` 从局域网访问 HTTP 200 ✅

---

## 遗留事项

1. **安装向导订阅字段**：fpk 内 wizard/config 含订阅两字段，但 fnOS 向导仅在全新安装（无残留数据）时展示。常规入口为 App Center → 应用设置。待在完全干净的环境验证一次向导展示。
2. **内核下载重试**：可考虑 `/api/update_core` 失败自动重试 2 次。
3. **GitHub 加速**：可选支持镜像源 fallback（如 ghproxy），提升弱网环境成功率。
