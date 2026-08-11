<img width="1306" height="843" alt="20260811-192929" src="https://github.com/user-attachments/assets/c46ff9d2-d7df-4b34-a07f-e85866b48aaa" />

# Mihomo Core (mihomo-core-fnos)

[![GitHub release](https://img.shields.io/github/v/release/techysy/mihomo-core-fnos?label=Latest&color=blue)](https://github.com/techysy/mihomo-core-fnos/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/techysy/mihomo-core-fnos/blob/main/LICENSE)
[![mihomo: GPLv3](https://img.shields.io/badge/mihomo-GPLv3-blueviolet.svg)](https://github.com/MetaCubeX/mihomo)
[![fnOS](https://img.shields.io/badge/fnOS-1.1.31xx+-orange.svg)](https://developer.fnnas.com/docs/guide)
[![Arch: x86_64](https://img.shields.io/badge/Arch-x86__64-lightgrey.svg)]()

fnOS 应用：**独立的 mihomo 内核代理服务**（自启），配合 **MetaCubeXD 面板** 控制节点。

- 混合代理端口：`7890`
- Clash API（控制端）：`9090`
- 自带状态页（桌面入口）：`9092`

---

## 特性

- ✅ 独立 mihomo 内核服务，随 fnOS 开机自启
- ✅ 纯服务 + 自带状态页（显示内核在线/版本/节点数/规则数）
- ✅ 配合 MetaCubeXD 面板（或其他 Clash 客户端）管理节点
- ✅ geoip 数据预置（避免内核首次启动从公网下载失败）
- ✅ 遵循 mihomo 的 GPLv3 许可证

## 架构

```
┌─────────────┐      ┌───────────────────────┐
│ MetaCubeXD  │────▶ │  mihomo-core (本应用)  │
│ 面板 :9091  │ 9090 │   mihomo 内核          │
└─────────────┘      │   mixed 7890 (代理)    │
                     │   状态页 9092 (桌面)   │
                     └───────────────────────┘
```

- **mihomo-core**：跑 mihomo 内核，提供代理（7890）和控制 API（9090）
- **MetaCubeXD**（单独 app）：纯前端面板，连接 9090 添加/管理节点

## 端口

| 端口 | 用途 |
|------|------|
| `7890` | 混合代理（HTTP/SOCKS5，系统代理出口） |
| `9090` | Clash API（MetaCubeXD 面板控制） |
| `9092` | 自带状态页（fnOS 桌面入口） |

## 安装

1. 从 [Releases](https://github.com/techysy/mihomo-core-fnos/releases) 下载 `mihomo-core-x.x.x.fpk`
2. 在 fnOS App Center **手动安装**（安装时有协议同意）
3. 打开桌面 **Mihomo Core** 查看内核状态
4. 打开 **MetaCubeXD** 面板，填 API 地址：
   ```
   http://<NAS-IP>:9090
   ```
5. 在面板里添加你的节点/订阅，mihomo-core 自动加载

> ⚠️ API 地址请用 **NAS 的局域网 IP**（如 `192.168.31.101:9090`），不要用 `127.0.0.1`（那是用户设备自己）。

## 端口被占用 / 残留进程处理

如果卸载/重装后提示 `端口被占用`（9090 / 7890 / 9092），说明有残留进程。SSH 到 NAS 执行：

```bash
# 杀掉残留 mihomo / 状态页进程
pkill -9 -f mihomo
pkill -9 -f status_server.py

# 强制释放端口（任选其一）
fuser -k 9090/tcp 7890/tcp 9092/tcp    # 若系统有 fuser
# 或用 lsof 找 PID 再 kill
lsof -i :9090
kill -9 <PID>

# 确认端口已释放（应无输出）
ss -tln | grep -E ':9090|:7890|:9092'
```

> 💡 卸载后应用已自动清理进程；若仍占用，多半是手动测试残留，用上面命令释放即可。

## 配置

- 配置文件：`<数据目录>/config.yaml`（首次启动从包内复制）
- 添加节点后，在 App Center 里重启 mihomo-core 让配置生效（或直接在面板触发重载）
- 代理端口 `7890`、Clash API `9090` 如需修改，编辑 config.yaml 后重启

## 源码构建

### 需要准备的文件

`.gitignore` 已排除大文件，clone 后需自行准备：

| 文件 | 说明 | 来源 |
|------|------|------|
| `app/mihomo` | mihomo 内核二进制（x86-64） | 从 [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) Releases 下载 |
| `app/geoip.metadb` | MaxMind GeoIP 数据库 | 从 mihomo/Clash geoip 源获取 |

### 构建

```bash
# 在 NAS 构建目录
cd /vol1/1000/fnOS\ App/build/mihomo-core-fnos/
fnpack build
# 输出 mihomo-core.fpk
```

## 许可证

- **mihomo 内核**：GPLv3（见 `GPL-3.0.txt`），来源 [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo)
- **本应用**（打包脚本/状态页/配置）：MIT（见 `LICENSE`）

## 相关项目

- [metacubexd-fnos](https://github.com/techysy/metacubexd-fnos) — MetaCubeXD 面板（fnOS 版，MIT）— 用这个面板控制本内核
- [mihomo](https://github.com/MetaCubeX/mihomo) — 内核（GPLv3）
- [MetaCubeXD 上游](https://github.com/MetaCubeX/metacubexd) — 面板前端（MIT）
