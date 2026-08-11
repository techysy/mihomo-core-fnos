# Mihomo Core 发布流程 (RELEASE)

本文件记录 mihomo-core 的标准发版流程与踩坑经验，**每次发版必须按此执行**。

---

## 版本号规则

- 格式：`1.0.x`（主.次.修订）
- 每次**较大功能改动**升一版（如 1.0.3 → 1.0.4）

### 版本单一来源（3 处必须同步）

| 文件 | 位置 | 说明 |
|------|------|------|
| `manifest` | `version = 1.0.x` | fnOS App Center 显示版本 |
| `app/status_server.py` | `APP_VERSION = "1.0.x"` | 状态页显示版本 |
| `cmd/main` | `APP_VERSION:-1.0.x` | 启动时传给状态页 |

> ⚠️ 三处不一致会导致「App Center 显示 1.0.4，但状态页还是 v1.0.3」。

---

## 完整发版流程

### 1. 改版本号（3 处）
```bash
sed -i 's/^version.*/version               = 1.0.4/' manifest
sed -i 's/"MIHOMO_APP_VERSION", "1.0.3"/"MIHOMO_APP_VERSION", "1.0.4"/' app/status_server.py
sed -i 's/MIHOMO_APP_VERSION:-1.0.3/MIHOMO_APP_VERSION:-1.0.4/g' cmd/main
```

### 2. 更新文档
- `CHANGELOG.md`：顶部加新版本条目
- `README.md` / `README.en.md`：如有功能变化同步
- `docs/fnforum-post.md`：版本引用同步（`mihomo-core-1.0.x-iframe.fpk`）

### 3. 同步到 101 构建目录
```bash
tar czf - cmd app manifest wizard config LICENSE GPL-3.0.txt scripts/build.sh 2>/dev/null | \
  ssh yangyu@192.168.31.101 "cd '/vol1/1000/fnOS App/build/mihomo-core-fnos/' && tar xzf - && chmod +x cmd/* app/*.py"
```

### 4. 打包双版本（url + iframe）
在 101 构建目录：
```bash
# iframe 版（config type=iframe）
python3 -c "import json;p='app/ui/config';d=json.load(open(p));d['.url']['mihomo-core.Application']['type']='iframe';json.dump(d,open(p,'w'),ensure_ascii=False,indent=2)"
fnpack build && mv mihomo-core.fpk mihomo-core-1.0.4-iframe.fpk
# url 版（config type=url）
python3 -c "import json;p='app/ui/config';d=json.load(open(p));d['.url']['mihomo-core.Application']['type']='url';json.dump(d,open(p,'w'),ensure_ascii=False,indent=2)"
fnpack build && mv mihomo-core.fpk mihomo-core-1.0.4.fpk
```

### 5. 交付 + 部署验证
```bash
cp mihomo-core-1.0.4.fpk mihomo-core-1.0.4-iframe.fpk '/vol1/1000/fnOS App/fpk/mihomo-core/'
# 卸载重装 iframe 版（见下方「部署方式」）
```

### 6. 发布 Release
```bash
scp "yangyu@192.168.31.101:/vol1/1000/fnOS App/fpk/mihomo-core/mihomo-core-1.0.4.fpk" /tmp/
scp "yangyu@192.168.31.101:/vol1/1000/fnOS App/fpk/mihomo-core/mihomo-core-1.0.4-iframe.fpk" /tmp/
gh release create v1.0.4 /tmp/mihomo-core-1.0.4.fpk /tmp/mihomo-core-1.0.4-iframe.fpk \
  --title "mihomo-core 1.0.4" --notes "..."
```

### 7. 提交 git
```bash
git add . && git commit -m "release: v1.0.4 — ..." && git push origin master
```

---

## 部署方式（重要）

> ⚠️ **状态页进程是 mihomo-core 用户启动，yangyu 无 sudo 权限无法杀掉**。
> 直接 `cp` 更新运行目录 status_server.py 后，旧进程仍用旧代码 → 状态页版本/功能不更新。

**最可靠：卸载重装**（fnOS 用 root 清理旧进程，安装新代码）。
```bash
TRIM_CLI_SESSION_STORAGE=file /tmp/trim-cli --host localhost --port 5666 --scheme ws --allow-insecure-ws app uninstall mihomo-core --yes
TRIM_CLI_SESSION_STORAGE=file /tmp/trim-cli --host localhost --port 5666 --scheme ws --allow-insecure-ws app install-fpk --remote-path '<fpk路径>' --volume-id 4 --accept-license --yes
```

> 直接 `cmd/main` 手动启动会因未传 `TRIM_APPDEST` 用错 APP_DIR（`/var/apps/mihomo-core` 而非 `/vol4/@appcenter/mihomo-core`），导致找不到二进制——**不要手动跑 cmd/main**。

---

## 常见坑

1. **版本不同步**：manifest / status_server.py / cmd/main 三处不一致 → 状态页版本旧
2. **状态页不更新**：只 cp 运行目录但没重启进程 → 旧进程跑旧代码 → 必须卸载重装
3. **wizard/config 格式**：必须是 `[{ "stepTitle": "...", "items": [...] }]`，缺 `stepTitle` 会打包失败
4. **proxy-providers 订阅**：应用设置填订阅链接 → config_callback 写 `subscription_url` → ensure_config 写入 config.yaml → 重启拉取
5. **状态页订阅状态**：`/providers/proxies` 会包含内置 proxy-group（Compatible），需过滤掉，只显示 HTTP/File 订阅

---

## 订阅功能（1.0.4 起）

- 应用设置里填订阅链接（`subscription_url`）
- `cmd/config_callback` 保存到 `@appdata/mihomo-core/subscription_url`
- `cmd/main` ensure_config 写入 config.yaml 的 `proxy-providers`
- 状态页 `/api/status` 返回 `subscriptions`（provider + 节点数）
