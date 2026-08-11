# Mihomo Core (mihomo-core-fnos)

An fnOS app: **standalone mihomo proxy core** (auto-start) controlled via the **MetaCubeXD** panel.

- Mixed proxy port: `7890`
- Clash API (control): `9090`
- Built-in status page (desktop entry): `9092`

---

## Features

- ✅ Standalone mihomo core, auto-starts with fnOS
- ✅ Service + built-in status page (core online / version / proxies / rules)
- ✅ Works with MetaCubeXD panel (or any Clash client) for node management
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

1. Install `mihomo-core` in fnOS App Center (license agreement shown)
2. Open **Mihomo Core** on the desktop to view core status
3. Open **MetaCubeXD** panel, set API address:
   ```
   http://<NAS-IP>:9090
   ```
4. Add your nodes/subscription — mihomo-core loads them automatically

> ⚠️ Use the **NAS LAN IP** (e.g. `192.168.31.101:9090`), not `127.0.0.1` (that's the user's own device).

## Config

- Config file: `<data-dir>/config.yaml` (copied from the package on first start)
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

## Related

- [metacubexd-fnos](https://github.com/techysy/metacubexd-fnos) — MetaCubeXD panel (fnOS, MIT) — use this panel to control this core
- [mihomo](https://github.com/MetaCubeX/mihomo) — core (GPLv3)
- [MetaCubeXD upstream](https://github.com/MetaCubeX/metacubexd) — panel frontend (GPLv3)
