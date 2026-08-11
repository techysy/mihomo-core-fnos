# 🚀 Mihomo Core — 飞牛 NAS 独立的 mihomo 内核代理服务

> 让飞牛 NAS 成为局域网内的**灵活代理网关**，满足日常网络场景需求

---

## 📦 简介

**Mihomo Core** 是飞牛 fnOS 上的一个**独立 mihomo（Clash Meta）内核代理服务**，开机自启，不占用 App Center 面板资源。配合 **MetaCubeXD** 面板即可灵活管理代理节点，把 NAS 打造成局域网代理网关。

- 🖥️ 自带**状态页**（桌面图标点开即看内核运行状态）
- 🔄 随飞牛**开机自启**，稳定运行
- 🧩 独立内核服务，不绑定面板，想用哪个面板都行

---

## 🎯 适用场景（日常合法需求）

**代理是日常网络工具，合法合规地服务于工作与生活：**

- 🧑‍🤝‍🧑 **跨地域访问**：比如广东的朋友需要外地节点 IP，访问异地内容、避免地域限制/地域歧视
- 💼 **办公环境运维**：日常办公需要走公司/单位的网络代理，统一出口、便于内网运维管理
- 🌐 **多地区选路**：同一业务需要不同地区出口，按规则灵活切换节点
- 🏠 **家庭网关**：全屋设备统一走 NAS 代理出口，管理方便

> ⚖️ 请遵守当地法律法规，将代理用于合法的网络访问与运维场景。

---

## ✨ 特性

| 特性 | 说明 |
|------|------|
| ⚡ 独立 mihomo 内核 | 纯服务，开机自启，稳定 |
| 📊 自带状态页 | 显示内核在线 / 版本 / 节点数 / 规则数 |
| 🧭 配合 MetaCubeXD | 优雅的面板，管理节点、规则、连接 |
| 🌍 局域网代理 | mixed 7890，全屋设备可走 NAS 代理 |
| 📦 geoip 预置 | 首次启动无需公网下载，开箱即用 |
| ⚖️ 协议合规 | 附 GPLv3（mihomo）+ MIT（应用） |

---

## 🔌 端口说明

| 端口 | 用途 |
|------|------|
| `7890` | 混合代理（HTTP / SOCKS5，系统代理出口） |
| `9090` | Clash API（MetaCubeXD 面板控制） |
| `9092` | 自带状态页（桌面入口） |

---

## 📥 安装方法

### 方式一：App Center 安装（推荐）

1. 到 **[Releases 页面](https://github.com/techysy/mihomo-core-fnos/releases)** 下载最新版
   - `mihomo-core-x.x.x.fpk`（url 版）
   - 或 `mihomo-core-x.x.x-iframe.fpk`（桌面窗口版，推荐）
2. 飞牛 App Center → **手动安装** → 选择 fpk 文件
3. 安装时有**协议同意**，同意后自动完成

### 方式二：命令行安装（进阶）

```bash
# 需要 fnOS App Center 支持 install 命令
fnapp install /path/to/mihomo-core-1.0.3-iframe.fpk
```

---

## 🎯 使用教程

### 第一步：查看内核状态

桌面打开 **Mihomo Core** → 看到状态页：
- Clash API 在线 / 离线
- 内核版本（如 v1.19.29）
- 节点数 / 规则数

### 第二步：用 MetaCubeXD 面板控制

1. 打开 **MetaCubeXD** 面板（[另一独立 App](https://github.com/techysy/metacubexd-fnos)）
2. 填 API 地址：
   ```
   http://<你的NAS-IP>:9090
   ```
   > ⚠️ 用 NAS 的**局域网 IP**（如 `192.168.31.101`），不要用 `127.0.0.1`
3. 在面板里**添加订阅 / 节点**
4. 即可管理节点、切换规则、查看连接

### 第三步：设备走代理

把设备（手机/电脑）的 HTTP 代理指向 NAS：
```
代理地址：192.168.31.101
代理端口：7890
```

---

## 🖼️ 界面预览

| 状态页 | MetaCubeXD 面板 |
|--------|----------------|
| 显示内核在线状态、版本、节点/规则数 | 管理节点、规则、连接 |

> （可自行补充实际截图）

---

## 🛠️ 常见问题（FAQ）

### Q：重装提示"端口被占用"？
卸载/重装后若提示 `9090 / 7890 / 9092` 端口被占用，是残留进程。SSH 到 NAS：

```bash
pkill -9 -f mihomo
pkill -9 -f status_server.py
fuser -k 9090/tcp 7890/tcp 9092/tcp    # 释放端口
ss -tln | grep -E ':9090|:7890|:9092'  # 确认已释放（应无输出）
```

### Q：状态页显示"Clash API 离线"？
- 确认内核已启动（App Center 里状态为"运行中"）
- 检查 `9090` 端口是否被占用

### Q：MetaCubeXD 连不上？
- 用 NAS 的局域网 IP，不要用 `127.0.0.1`
- 确认 9090 端口可达（局域网内其他设备能 ping 通 NAS）

---

## 📄 许可证

- **mihomo 内核**：GPLv3（见 `GPL-3.0.txt`），来源 [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo)
- **本应用**（打包脚本/状态页/配置）：MIT（见 `LICENSE`）

---

## 🔗 相关链接

- 📦 [Releases 下载](https://github.com/techysy/mihomo-core-fnos/releases)
- 🖥️ [MetaCubeXD 面板](https://github.com/techysy/metacubexd-fnos)
- 📖 [项目源码](https://github.com/techysy/mihomo-core-fnos)
- ⚙️ [mihomo 内核](https://github.com/MetaCubeX/mihomo)

---

> 💡 有任何问题或建议，欢迎在 GitHub Issues 反馈！
>
> 🌟 觉得好用的话，欢迎给项目点个 **Star** 支持一下，感谢！

<a href="https://github.com/techysy/mihomo-core-fnos" target="_blank">
  <img src="https://img.shields.io/github/stars/techysy/mihomo-core-fnos?style=for-the-badge&logo=github" alt="GitHub stars" />
</a>
