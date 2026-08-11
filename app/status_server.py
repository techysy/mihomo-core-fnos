#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mihomo-core 状态页 — 零依赖 (stdlib http.server)，监听 9092。
显示 mihomo 内核状态：Clash API (:9090) 是否在线、版本、代理端口、规则/节点数。
"""
import json
import os
import subprocess
import urllib.request
import http.server
import socketserver

PORT = int(os.environ.get("MIHOMO_STATUS_PORT", "9092"))
CLASH_API = os.environ.get("MIHOMO_CLASH_API", "http://127.0.0.1:9090")
APP_VERSION = os.environ.get("MIHOMO_APP_VERSION", "1.0.2")

BRAND = "#ff6a00"  # 橙色主题

def get_lan_ip():
    """获取本机局域网 IP（非 loopback），用于提示面板连接地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("223.5.5.5", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


LAN_IP = get_lan_ip()

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mihomo Core</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f6f8;color:#1a1a1a;padding:24px}
  .wrap{max-width:680px;margin:0 auto}
  .brand{font-size:22px;font-weight:700;color:#1a1a1a;margin-bottom:4px}
  .brand span{color:%(BRAND)s}
  .brand .ver{font-size:12px;color:#888;font-weight:600;margin-left:6px}
  .sub{color:#888;font-size:13px;margin-bottom:20px}
  .card{background:#fff;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.06);padding:20px;margin-bottom:16px}
  .row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0}
  .row:last-child{border-bottom:none}
  .k{color:#888;font-size:14px}
  .v{font-weight:600;font-size:14px}
  .pill{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600}
  .ok{background:#e6f6ec;color:#1a9e4e}
  .down{background:#fdeaea;color:#d93025}
  .h{font-size:14px;font-weight:700;margin-bottom:10px}
</style></head><body>
<div class="wrap">
  <div class="brand">Mihomo <span>Core</span> <span class="ver">v%(APP_VERSION)s</span></div>
  <div class="sub">mihomo 内核代理服务 · mixed 7890 · Clash API 9090</div>
  <div class="card">
    <div class="h">内核状态</div>
    <div class="row"><span class="k">Clash API (:9090)</span><span id="api" class="pill down">检测中…</span></div>
    <div class="row"><span class="k">内核版本</span><span id="ver" class="v">—</span></div>
    <div class="row"><span class="k">模式</span><span id="mode" class="v">—</span></div>
    <div class="row"><span class="k">节点数</span><span id="nodes" class="v">—</span></div>
    <div class="row"><span class="k">规则数</span><span id="rules" class="v">—</span></div>
    <div class="row"><span class="k">混合代理端口</span><span class="v">7890</span></div>
  </div>
  <div class="card" style="text-align:center;color:#888;font-size:13px">
    用 <a href="https://github.com/techysy/metacubexd-fnos" target="_blank" rel="noopener" style="color:#ff6a00;font-weight:600;text-decoration:none" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">MetaCubeXD</a> 面板控制节点：打开面板 → 填 API 地址 <code>http://%(HOST)s:9090</code>
  </div>
</div>
<script>
async function load(){
  try{
    const r = await fetch('/api/status');
    const d = await r.json();
    const api=document.getElementById('api');
    if(d.ok){ api.textContent='在线'; api.className='pill ok'; }
    else { api.textContent='离线'; api.className='pill down'; }
    document.getElementById('ver').textContent = d.version||'—';
    document.getElementById('mode').textContent = d.mode||'—';
    document.getElementById('nodes').textContent = d.proxies||'—';
    document.getElementById('rules').textContent = d.rules||'—';
  }catch(e){}
}
load(); setInterval(load, 5000);
</script></body></html>
""" % {"BRAND": BRAND, "HOST": LAN_IP, "APP_VERSION": APP_VERSION}


def clash(path, default=None):
    """调 Clash API，失败返回 default"""
    try:
        req = urllib.request.Request(CLASH_API + path, headers={"User-Agent": "mihomo-core"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return default


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静默
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/status":
            ver = clash("/version")
            cfg = clash("/configs")
            proxies = clash("/proxies")
            data = {
                "ok": ver is not None,
                "app_version": APP_VERSION,
                "version": (ver or {}).get("version", ""),
                "mode": (cfg or {}).get("mode", ""),
                "proxies": len((proxies or {}).get("proxies", {}) or {}),
                "rules": (cfg or {}).get("rules_count", 0),
            }
            body = json.dumps(data).encode()
            self._send(200, body, "application/json; charset=utf-8")
        else:
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    httpd = Server(("0.0.0.0", PORT), Handler)
    httpd.serve_forever()
