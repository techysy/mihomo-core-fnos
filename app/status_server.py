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
APP_VERSION = os.environ.get("MIHOMO_APP_VERSION", "1.1.1")
def _default_data_dir():
    """从 status_server.py 所在位置推导数据目录（避免硬编码存储卷路径）。
    脚本位置: <vol>/@appcenter/<app>[/target]/status_server.py
    数据目录: <vol>/@appdata/<app>
    """
    script = os.path.abspath(__file__)
    parts = script.split(os.sep)
    if "@appcenter" in parts:
        idx = parts.index("@appcenter")
        if idx + 1 < len(parts):
            vol = os.sep.join(parts[:idx])
            app = parts[idx + 1]
            if vol and app:
                return os.path.join(vol, "@appdata", app)
    # 兜底: 从当前目录向上找 @appdata/<app>
    d = os.path.dirname(script)
    for _ in range(4):
        if os.path.basename(os.path.dirname(d)) == "@appdata":
            return os.path.dirname(d)
        d = os.path.dirname(d)
    return os.path.join(os.path.dirname(script), "@appdata")


DATA_DIR = os.environ.get("MIHOMO_DATA_DIR") or _default_data_dir()

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
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f6f8;color:#1a1a1a;padding:24px;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .wrap{width:45%%;max-width:1200px;transform:translateY(-5%%)}
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
  /* 移动端简洁文案默认隐藏，桌面端完整文案 */
  .meta-short{display:none}
  @media (max-width:600px){
    body{padding:16px}
    .wrap{width:90%%;transform:translateY(-13%%)}
    .brand{font-size:19px}
    .card{padding:14px}
    .row{padding:7px 0}
    .k,.v{font-size:13px}
    /* 说明文字移动端适配：避免被挤成多排 */
    .card .meta-tip{font-size:12px;line-height:1.6}
    /* 移动端：隐藏完整文案，显示简洁文案 */
    .meta-full{display:none}
    .meta-short{display:block}
  }
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
    <div class="row"><span class="k">订阅</span><span id="subs" class="v" style="cursor:pointer" title="点击手动获取订阅">未配置</span></div>
    <div class="row"><span class="k">混合代理端口</span><span class="v">7890</span></div>
  </div>
  <div class="card meta-tip" style="text-align:center;color:#888;font-size:13px;line-height:1.7">
    <span class="meta-full"><a href="https://github.com/techysy/metacubexd-fnos" target="_blank" rel="noopener" style="color:#ff6a00;font-weight:600;text-decoration:none" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">MetaCubeXD</a> 面板用于控制节点 若未安装，可点击橙色文字下载<br>
    已安装则在面板中填 API 地址 <a href="javascript:void(0)" onclick="copyApi()" title="点击复制" style="color:#ff6a00;font-weight:600;text-decoration:none;cursor:pointer" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">http://%(HOST)s:9090</a> <span id="copiedTip" style="color:#1a9e4e;font-size:12px"></span></span>
    <span class="meta-short"><a href="https://github.com/techysy/metacubexd-fnos" target="_blank" rel="noopener" style="color:#ff6a00;font-weight:600;text-decoration:none" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">MetaCubeXD</a> 面板用于控制节点<br>
    API 地址 <a href="javascript:void(0)" onclick="copyApi()" title="点击复制" style="color:#ff6a00;font-weight:600;text-decoration:none;cursor:pointer" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">http://%(HOST)s:9090</a> <span id="copiedTip2" style="color:#1a9e4e;font-size:12px"></span></span>
  </div>
</div>
<script>
// 复制 API 地址到剪贴板
function copyApi(){
  var url = 'http://%(HOST)s:9090';
  var tip = document.getElementById('copiedTip');
  var tip2 = document.getElementById('copiedTip2');
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(url).then(function(){ showCopied(tip); showCopied(tip2); }, function(){ fallbackCopy(url, tip); fallbackCopy(url, tip2); });
  } else {
    fallbackCopy(url, tip);
    fallbackCopy(url, tip2);
  }
}
function fallbackCopy(text, tip){
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try{ document.execCommand('copy'); showCopied(tip); }catch(e){}
  document.body.removeChild(ta);
}
function showCopied(tip){
  if(!tip) return;
  tip.textContent = '已复制 ✓';
  setTimeout(function(){ tip.textContent = ''; }, 2000);
}
var subUpdating = false;
async function updateSub(){
  if(subUpdating) return;
  subUpdating = true;
  var subsEl = document.getElementById('subs');
  subsEl.innerHTML = '<span style="color:#888">获取中…</span>';
  try{
    const r = await fetch('/api/update_subscription');
    const d = await r.json();
    if(d.ok){ subsEl.innerHTML = '<span style="color:#1a9e4e">✓ 已更新 ' + (d.nodes||'') + ' 节点</span>'; }
    else { subsEl.innerHTML = '<span style="color:#d93025">✗ ' + (d.message||'失败') + '</span>'; }
    setTimeout(load, 900);
  }catch(e){
    subsEl.innerHTML = '<span style="color:#d93025">✗ 请求失败</span>';
  }
  subUpdating = false;
}
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
    // 订阅状态: 未配置灰 / 有节点绿 / 无节点灰(可点击重试, 首次自动获取)
    const subsEl = document.getElementById('subs');
    subsEl.style.cursor = 'pointer';
    subsEl.onclick = updateSub;
    subsEl.title = '点击手动获取订阅';
    if(d.subscription_configured){
      const name = d.subscription_name || '订阅配置';
      const n = d.sub_proxies || 0;
      if(n > 0){
        subsEl.innerHTML = '<span style="color:#1a9e4e">' + name + ' · 已启用</span>';
        window._subAuto = true;
      } else {
        subsEl.innerHTML = '<span style="color:#999">' + name + ' · 未获取到节点</span>';
        if(!window._subAuto){
          window._subAuto = true;
          setTimeout(updateSub, 400);
        }
      }
    } else {
      subsEl.innerHTML = '<span style="color:#999">未配置</span>';
      window._subAuto = true;
    }
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

    def _update_subscription(self):
        """拉取订阅 → 写 config.yaml → 热重载 mihomo (Clash API PUT /configs)."""
        import re as _re, urllib.error
        sub_path = os.path.join(DATA_DIR, "subscription_url")
        if not os.path.isfile(sub_path):
            return {"ok": False, "message": "未配置订阅链接 (subscription_url 不存在)"}
        try:
            with open(sub_path, encoding="utf-8") as f:
                subdata = f.read().strip()
            url = subdata.split("|", 1)[1] if "|" in subdata else subdata
            url = url.strip()
            if not url:
                return {"ok": False, "message": "订阅链接为空"}
            req = urllib.request.Request(url, headers={"User-Agent": "clash.meta", "Accept": "application/yaml"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read().decode("utf-8", errors="replace")
            if not data.strip():
                return {"ok": False, "message": "订阅返回为空"}
            # 强制本应用端口
            data = _re.sub(r"(?m)^mixed-port:.*$", "mixed-port: 7890", data)
            data = _re.sub(r"(?m)^port:.*$", "port: 7890", data)
            data = _re.sub(r"(?m)^socks-port:.*$", "socks-port: 7890", data)
            data = _re.sub(r"(?m)^external-controller:.*$", "external-controller: '0.0.0.0:9090'", data)
            cfg_path = os.path.join(DATA_DIR, "config.yaml")
            open(cfg_path, "w", encoding="utf-8").write(data)
            # 热重载 mihomo (不重启进程)
            reloaded = False
            try:
                body = json.dumps({"path": cfg_path}).encode()
                req2 = urllib.request.Request(CLASH_API + "/configs?force=true", data=body,
                                              headers={"Content-Type": "application/json", "User-Agent": "mihomo-core"},
                                              method="PUT")
                with urllib.request.urlopen(req2, timeout=10) as resp:
                    reloaded = resp.status in (200, 204)
            except Exception as e:
                return {"ok": False, "message": "配置已写入但重载失败: %s" % e, "nodes": len(data.split(chr(10)))}
            # 统计节点数
            import re as _re2
            nodes = len(_re2.findall(r"^\s*-\s*name:", data, _re2.M))
            return {"ok": True, "message": "订阅更新成功", "nodes": nodes, "reloaded": reloaded}
        except urllib.error.HTTPError as e:
            return {"ok": False, "message": "拉取失败 HTTP %s" % e.code}
        except Exception as e:
            return {"ok": False, "message": "%s" % e}

    def do_GET(self):  # noqa: N802
        if self.path == "/api/update_subscription":
            result = self._update_subscription()
            body = json.dumps(result).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path == "/api/status":
            ver = clash("/version")
            cfg = clash("/configs")
            proxies = clash("/proxies")
            rules_api = clash("/rules") or {}
            providers = clash("/providers/proxies") or {}
            # 订阅配置检测：若应用设置里配了订阅链接（subscription_url 文件存在），则订阅作为完整配置启用
            sub_configured = os.path.isfile(os.path.join(DATA_DIR, "subscription_url"))
            sub_name = ""
            try:
                with open(os.path.join(DATA_DIR, "subscription_url"), encoding="utf-8") as f:
                    first = f.read().strip().splitlines()
                    if first and "|" in first[0]:
                        sub_name = first[0].split("|", 1)[0].strip()
            except Exception:
                pass
            # 订阅 (proxy-providers) 状态：只统计真正的订阅(HTTP/File)，排除内置 proxy-group(Compatible)
            subs = []
            for name, prov in (providers.get("providers") or {}).items():
                vt = prov.get("vehicleType", prov.get("vehicle-type", ""))
                if vt in ("Compatible", "Direct"):
                    continue
                subs.append({
                    "name": name,
                    "type": prov.get("type", ""),
                    "vehicle_type": vt,
                    "proxies": len(prov.get("proxies", []) or []),
                    "updated_at": prov.get("updatedAt", prov.get("updated_at", "")),
                    "error": prov.get("error", ""),
                })
            # 订阅节点数 (完整配置模式: config.yaml 的 proxies 段节点数)
            sub_proxies = 0
            if sub_configured:
                try:
                    import re as _re3
                    with open(os.path.join(DATA_DIR, "config.yaml"), encoding="utf-8") as f:
                        _cfg = f.read()
                    _lines = _cfg.splitlines()
                    _in = False
                    for _ln in _lines:
                        if _ln.startswith("proxies:"):
                            _in = True; continue
                        if _in and _ln.startswith("proxy-groups:"):
                            break
                        if _in and _re3.match(r"^\s*-\s*name:", _ln):
                            sub_proxies += 1
                except Exception:
                    pass
            data = {
                "ok": ver is not None,
                "app_version": APP_VERSION,
                "version": (ver or {}).get("version", ""),
                "mode": (cfg or {}).get("mode", ""),
                "proxies": len((proxies or {}).get("proxies", {}) or {}),
                "rules": len(rules_api.get("rules", []) or []),
                "subscriptions": subs,
                "subscription_configured": sub_configured,
                "subscription_name": sub_name,
                "sub_proxies": sub_proxies,
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
