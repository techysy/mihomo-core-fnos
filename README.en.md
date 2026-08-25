# Mihomo Core (mihomo-core-fnos)

[![GitHub release](https://img.shields.io/github/v/release/techysy/mihomo-core-fnos?label=Latest&color=blue)](https://github.com/techysy/mihomo-core-fnos/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/techysy/mihomo-core-fnos/blob/main/LICENSE)
[![mihomo: GPLv3](https://img.shields.io/badge/mihomo-GPLv3-blueviolet.svg)](https://github.com/MetaCubeX/mihomo)
[![fnOS](https://img.shields.io/badge/fnOS-1.1.31xx+-orange.svg)](https://developer.fnnas.com/docs/guide)
[![Arch: x86_64](https://img.shields.io/badge/Arch-x86__64-lightgrey.svg)]()

An fnOS app: **standalone mihomo proxy core** (auto-start) controlled via the **MetaCubeXD** panel.

- Mixed proxy port: `7890`
- Clash API (control): `9090`
- Built-in status page (desktop entry): `9092`

---

## Features

- ✅ Standalone mihomo core, auto-starts with fnOS
- ✅ Service + built-in status page (core online / version / proxies / rules)
- ✅ Works with MetaCubeXD panel (or any Clash client) for node management
- ✅ Subscription config: fill URL in App Center app settings; auto-pull with hot-reload, forces `allow-lan: true`
- ✅ **Core hot update**: click the core version on the status page to upgrade to the latest GitHub release — no repackaging needed (v1.1.2+)
- ✅ Preseeded geoip data (avoids public-network download failure on first start)
- ✅ Respects mihomo's GPLv3 license

## Architecture

```
┌─────────────┐      ┌───────────────────────┐
│ MetaCubeXD  │────▶ │  mihomo-core (this)   │
│ panel :9091 │ 9090 │   mihomo core         │
└─────────────┘      │   mixed 7890 (proxy)  │
                     │   status 9092 (desktop)│
                     └───────────────────────┘
```

## Ports

| Port | Purpose |
|------|---------|
| `7890` | Mixed proxy (HTTP/SOCKS5 system proxy) |
| `9090` | Clash API (controlled by MetaCubeXD) |
| `9092` | Built-in status page (desktop entry) |

## Install

1. Download `mihomo-core-x.x.x.fpk` from [Releases](https://github.com/techysy/mihomo-core-fnos/releases)
2. Install it manually in fnOS App Center (license agreement shown)
3. Open **Mihomo Core** on the desktop to view core status
4. Open **MetaCubeXD** panel, set API address:
   ```
   http://<NAS-IP>:9090
   ```
5. Add your nodes/subscription — mihomo-core loads them automatically

> ⚠️ Use the **NAS LAN IP** (e.g. `192.168.31.101:9090`), not `127.0.0.1` (that's the user's own device).

## Port in use / leftover process

If you get `port in use` (9090 / 7890 / 9092) after uninstall/reinstall, a process is leftover. SSH into the NAS and run:

```bash
# kill leftover mihomo / status page processes
pkill -9 -f mihomo
pkill -9 -f status_server.py

# force-free the ports (pick one)
fuser -k 9090/tcp 7890/tcp 9092/tcp    # if fuser exists
# or find the PID with lsof and kill it
lsof -i :9090
kill -9 <PID>

# confirm ports are free (should output nothing)
ss -tln | grep -E ':9090|:7890|:9092'
```

> 💡 The app cleans up processes on uninstall; if still occupied, it's usually a leftover from manual testing — free it with the commands above.

## Config

- Config file: `<data-dir>/config.yaml` (copied from the package on first start)
- **Subscription**: enter your subscription URL in **App Center → App Settings**; it's written into the mihomo config and pulled on restart
- After adding nodes, restart mihomo-core in App Center to apply (or trigger reload in the panel)
- To change proxy `7890` / Clash API `9090`, edit config.yaml and restart

## Build from source

### Files to prepare

Large files are gitignored; prepare after clone:

| File | Description | Source |
|------|-------------|--------|
| `app/mihomo` | mihomo core binary (x86-64) | [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) Releases |
| `app/geoip.metadb` | MaxMind GeoIP database | mihomo/Clash geoip source |

### Build

```bash
cd /vol1/1000/fnOS\ App/build/mihomo-core-fnos/
fnpack build
# outputs mihomo-core.fpk
```

## License

- **mihomo core**: GPLv3 (see `GPL-3.0.txt`), from [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo)
- **This app** (packaging scripts / status page / config): MIT (see `LICENSE`)

## Docs

- [User guide (中文)](docs/USER-GUIDE.md) — subscription config, core hot update, FAQ
- [v1.1.2 test report](docs/TEST-REPORT-v1.1.2.md) — full 7-item test record
- [v1.1.2 feasibility report](docs/FEASIBILITY-v1.1.2.md) — requirement analysis & live-path verification
- [Release process](docs/RELEASE.md) — versioning & release steps

## Related

- [metacubexd-fnos](https://github.com/techysy/metacubexd-fnos) — MetaCubeXD panel (fnOS, MIT) — use this panel to control this core
- [mihomo](https://github.com/MetaCubeX/mihomo) — core (GPLv3)
- [MetaCubeXD upstream](https://github.com/MetaCubeX/metacubexd) — panel frontend (MIT)
