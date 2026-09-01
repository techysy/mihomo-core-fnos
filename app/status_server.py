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
# MetaCubeXD 面板地址（mihomo 状态页触发面板更新/读版本）
PANEL_API = os.environ.get("MIHOMO_PANEL_API", "http://127.0.0.1:9091")
APP_VERSION = os.environ.get("MIHOMO_APP_VERSION", "1.1.4")
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
  <div class="brand">Mihomo <span>Core</span> <span class="ver" id="appVer" style="cursor:default">v%(APP_VERSION)s</span></div>
  <div class="sub">mihomo 内核代理服务 · mixed 7890 · Clash API 9090</div>
  <div class="card">
    <div class="h">内核状态</div>
    <div class="row"><span class="k">Clash API (:9090)</span><span id="api" class="pill down">检测中…</span></div>
    <div class="row"><span class="k">内核版本</span><span id="ver" class="v" style="cursor:pointer;color:#ff6a00" title="点击检查并更新内核" onclick="updateCore()">—</span></div>
    <div class="row"><span class="k">面板版本</span><span id="panelVer" class="v" style="cursor:pointer;color:#ff6a00" title="点击更新 MetaCubeXD 面板（无感，不中断代理）">—</span></div>
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
var coreUpdating = false;
async function updateCore(){
  if(coreUpdating) return;
  coreUpdating = true;
  var el = document.getElementById('ver');
  if(!confirm('检查并更新 mihomo 内核到最新版？更新过程会重启内核（代理中断几秒）')) { coreUpdating = false; return; }
  el.style.color = '#888';
  el.textContent = '检查更新中…';
  var ok = false, msg = '';
  try{
    const r = await fetch('/api/update_core');
    const d = await r.json();
    ok = !!d.ok; msg = d.message || (ok ? '更新完成' : '更新失败');
    if(ok && !d.uptodate){ /* 更新成功：load() 会刷新版本号 */ }
  }catch(e){
    msg = '请求失败';
  }
  coreUpdating = false;
  // 结果就地在版本号行显示 3 秒（绿=成功 红=失败），不弹窗
  el.textContent = msg;
  el.style.color = ok ? '#1a9e4e' : '#d93025';
  setTimeout(function(){ load(); }, 3000);
}
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
var panelUpdating = false;
async function updatePanel(){
  if(panelUpdating) return;
  panelUpdating = true;
  var el = document.getElementById('panelVer');
  if(!confirm('更新 MetaCubeXD 面板到最新版？更新过程不影响代理（面板短暂刷新）')) { panelUpdating = false; return; }
  el.style.color = '#888';
  el.textContent = '更新中…';
  var ok = false, msg = '';
  try{
    const r = await fetch('/api/update_panel');
    const d = await r.json();
    ok = !!d.ok; msg = d.message || (ok ? '面板已更新' : '更新失败');
  }catch(e){
    msg = '请求失败';
  }
  panelUpdating = false;
  el.textContent = msg;
  el.style.color = ok ? '#1a9e4e' : '#d93025';
  setTimeout(function(){ load(); }, 3000);
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
    // 面板版本（读 metacubexd 面板，localhost:9091）
    try{
      const pr = await fetch('/api/panel_version');
      const pd = await pr.json();
      const pv = document.getElementById('panelVer');
      if(pd.ok){
        pv.textContent = pd.version || '已安装';
        pv.onclick = updatePanel;
      } else {
        pv.textContent = '—';
        pv.onclick = null;
        pv.style.color = '#999';
      }
    }catch(e){}
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
            # 强制本应用端口 + 局域网访问（订阅默认 allow-lan: false 会断局域网代理）
            data = _re.sub(r"(?m)^mixed-port:.*$", "mixed-port: 7890", data)
            data = _re.sub(r"(?m)^port:.*$", "port: 7890", data)
            data = _re.sub(r"(?m)^socks-port:.*$", "socks-port: 7890", data)
            data = _re.sub(r"(?m)^external-controller:.*$", "external-controller: '0.0.0.0:9090'", data)
            data = _re.sub(r"(?m)^allow-lan:.*$", "allow-lan: true", data)
            if not _re.search(r"(?m)^allow-lan:", data):
                data = data.replace("mixed-port: 7890", "mixed-port: 7890\nallow-lan: true", 1)
            cfg_path = os.path.join(DATA_DIR, "config.yaml")

            # ── 注入用户自定义规则（独立文件 custom-rules.txt，订阅更新不覆盖）──
            # 用户的 AI / 中转站等自定义规则存在独立文件 custom-rules.txt，
            # 订阅刷新后通过 `type: file` rule-provider 重新注入 config.yaml，
            # 使自定义规则永久保留且独立落库（不被订阅覆盖）。
            _custom_path = os.path.join(DATA_DIR, "custom-rules.txt")
            if os.path.isfile(_custom_path) and os.path.getsize(_custom_path) > 0:
                try:
                    # 1) rules: 加 RULE-SET,custom（MATCH 兜底之前）
                    _lines = data.splitlines()
                    _out = []
                    _injected = False
                    for _line in _lines:
                        if not _injected and _line.strip().startswith("- ") and "MATCH" in _line:
                            _out.append("  - RULE-SET,custom,💬 Ai平台")
                            _injected = True
                        _out.append(_line)
                    if not _injected:
                        _out.append("  - RULE-SET,custom,💬 Ai平台")
                    data = "\n".join(_out)
                    # 2) rule-providers: 加 custom (type: file 本地文件)
                    _prov = '\n  custom:\n    type: file\n    behavior: classical\n    format: text\n    path: "%s"\n' % _custom_path
                    if "rule-providers:" in data:
                        data = data.replace("rule-providers:", "rule-providers:" + _prov, 1)
                    else:
                        data = data + "\nrule-providers:" + _prov
                except Exception:
                    pass

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

    def _update_core(self):
        """内核热更新：GitHub latest → 下载校验 → 原子替换 → 重启进程."""
        import re as _re, urllib.error, shutil, glob

        app_dir = os.path.dirname(os.path.abspath(__file__))
        # target/ fallback（fnOS TRIM_APPDEST 兼容，与 cmd/main 一致）
        core_bin = os.path.join(app_dir, "mihomo")
        if not os.path.isfile(core_bin) and os.path.isfile(os.path.join(app_dir, "target", "mihomo")):
            app_dir = os.path.join(app_dir, "target")
            core_bin = os.path.join(app_dir, "mihomo")

        # 当前版本
        try:
            out = subprocess.run([core_bin, "-v"], capture_output=True, text=True, timeout=10).stdout
            m = _re.search(r"v[\d.]+", out)
            cur_ver = (m.group(0) if m else "").lstrip("v")
        except Exception:
            cur_ver = ""

        def _gh(url, timeout=15):
            req = urllib.request.Request(url, headers={"User-Agent": "mihomo-core"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()

        # 1. 查 latest
        try:
            latest = json.loads(_gh("https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"))
        except Exception as e:
            return {"ok": False, "message": "查询 GitHub 失败: %s" % e}
        tag = latest.get("tag_name", "")  # e.g. v1.19.30
        new_ver = tag.lstrip("v")
        if not new_ver:
            return {"ok": False, "message": "未获取到最新版本号"}
        if new_ver == cur_ver:
            return {"ok": True, "message": "已是最新版本 v%s" % cur_ver, "version": cur_ver, "uptodate": True}

        # 2. 下载（临时文件，失败不动原内核）
        asset_name = "mihomo-linux-amd64-%s.gz" % tag
        asset_url = "https://github.com/MetaCubeX/mihomo/releases/download/%s/%s" % (tag, asset_name)
        tmp_gz = os.path.join(DATA_DIR, "mihomo.new.gz")
        tmp_bin = os.path.join(DATA_DIR, "mihomo.new")
        try:
            data = _gh(asset_url, timeout=300)
            with open(tmp_gz, "wb") as f:
                f.write(data)
        except Exception as e:
            self._cleanup_tmp(tmp_gz, tmp_bin)
            return {"ok": False, "message": "下载失败: %s" % e}

        # 3. 解压 + 校验
        try:
            import gzip
            with gzip.open(tmp_gz, "rb") as fin, open(tmp_bin, "wb") as fout:
                shutil.copyfileobj(fin, fout)
            os.chmod(tmp_bin, 0o755)
            out = subprocess.run([tmp_bin, "-v"], capture_output=True, text=True, timeout=10).stdout
            if new_ver not in out:
                raise RuntimeError("解压后版本校验失败: %s" % out[:80])
        except Exception as e:
            self._cleanup_tmp(tmp_gz, tmp_bin)
            return {"ok": False, "message": "解压/校验失败: %s" % e}

        # 4. 原子替换
        try:
            backup = core_bin + ".bak"
            if os.path.isfile(backup):
                os.remove(backup)
            os.rename(core_bin, backup)
            try:
                shutil.move(tmp_bin, core_bin)
            except Exception:
                os.rename(backup, core_bin)  # 回滚
                raise
            os.remove(backup)
        except Exception as e:
            self._cleanup_tmp(tmp_gz, tmp_bin)
            return {"ok": False, "message": "替换失败: %s" % e}
        finally:
            if os.path.isfile(tmp_gz):
                os.remove(tmp_gz)

        # 5. 重启内核进程（走 cmd/main restart；status_server 自身不受影响）
        main_sh = os.path.join(app_dir, "main")
        restart_hint = ""
        if not os.path.isfile(main_sh):
            # fnOS 部署形态: cmd 脚本在 /var/apps/<app>/cmd/main 或 target/cmd/main
            for cand in ("/var/apps/mihomo-core/cmd/main",
                         "/vol4/@appcenter/mihomo-core/target/cmd/main",
                         "/vol4/@appcenter/mihomo-core/cmd/main"):
                if os.path.isfile(cand):
                    main_sh = cand
                    break
        if os.path.isfile(main_sh):
            subprocess.Popen(["bash", main_sh, "restart"],
                             stdout=open(os.path.join(DATA_DIR, "mihomo.log"), "a"),
                             stderr=subprocess.STDOUT)
            restart_hint = "内核已重启加载新版本"
        else:
            restart_hint = "已替换二进制，请在应用管理重启应用后生效"

        return {"ok": True, "message": "v%s → v%s 更新完成。%s" % (cur_ver or "?", new_ver, restart_hint),
                "version": new_ver}

    @staticmethod
    def _cleanup_tmp(*paths):
        for p in paths:
            try:
                if p and os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass

    def do_GET(self):  # noqa: N802
        if self.path == "/api/update_subscription":
            result = self._update_subscription()
            body = json.dumps(result).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path == "/api/update_core":
            result = self._update_core()
            body = json.dumps(result).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path == "/api/custom_rules":
            path = self._custom_rules_file()
            rules = []
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        rules = [l.strip() for l in f if l.strip()]
                except Exception:
                    rules = []
            body = json.dumps({"ok": True, "rules": rules, "count": len(rules)}).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path == "/api/panel_version":
            # 读 MetaCubeXD 面板版本（面板提供 /__version 接口）
            try:
                req = urllib.request.Request(PANEL_API + "/__version")
                with urllib.request.urlopen(req, timeout=5) as r:
                    d = json.loads(r.read().decode("utf-8", errors="replace"))
                body = json.dumps({"ok": True, "version": d.get("version", ""), "panel": PANEL_API}).encode()
            except Exception as e:
                body = json.dumps({"ok": False, "message": "面板不可达: %s" % e}).encode()
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

    def _custom_rules_file(self):
        return os.path.join(DATA_DIR, "custom-rules.txt")

    def _ensure_custom_provider(self):
        """确保 config.yaml 注入 custom rule-provider + RULE-SET (幂等)。"""
        cfg_path = os.path.join(DATA_DIR, "config.yaml")
        if not os.path.isfile(cfg_path):
            return False
        try:
            data = open(cfg_path, encoding="utf-8").read()
            custom_path = self._custom_rules_file()
            changed = False
            if "RULE-SET,custom" not in data:
                lines = data.splitlines()
                out = []
                injected = False
                for line in lines:
                    if not injected and line.strip().startswith("- ") and "MATCH" in line:
                        out.append("  - RULE-SET,custom,💬 Ai平台")
                        injected = True
                    out.append(line)
                if not injected:
                    out.append("  - RULE-SET,custom,💬 Ai平台")
                data = "\n".join(out)
                changed = True
            if "custom:" not in data or "rule-providers:" not in data:
                prov = "\n  custom:\n    type: file\n    behavior: classical\n    format: text\n    path: \"%s\"\n" % custom_path
                if "rule-providers:" in data:
                    data = data.replace("rule-providers:", "rule-providers:" + prov, 1)
                else:
                    data = data + "\nrule-providers:" + prov
                changed = True
            if changed:
                open(cfg_path, "w", encoding="utf-8").write(data)
            return True
        except Exception:
            return False

    def _reload_mihomo(self):
        """热重载 mihomo 配置 (Clash API PUT /configs)."""
        try:
            cfg_path = os.path.join(DATA_DIR, "config.yaml")
            body = json.dumps({"path": cfg_path}).encode()
            req = urllib.request.Request(CLASH_API + "/configs?force=true", data=body,
                                         headers={"Content-Type": "application/json", "User-Agent": "mihomo-core"},
                                         method="PUT")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 204)
        except Exception:
            return False

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}
        if self.path == "/api/custom_rules":
            rule = (payload.get("rule") or "").strip()
            if not rule:
                self._send(400, json.dumps({"ok": False, "message": "rule 不能为空"}).encode(), "application/json; charset=utf-8")
                return
            # 规范化：未带类型前缀时默认按域名后缀 (DOMAIN-SUFFIX)
            if not rule.split(",", 1)[0].upper().startswith(("DOMAIN", "IP-", "RULE-SET", "GEOIP", "GEOSITE", "PROCESS", "MATCH")):
                rule = "DOMAIN-SUFFIX," + rule
            # 确保 config.yaml 有 custom provider，再追加规则
            self._ensure_custom_provider()
            path = self._custom_rules_file()
            with open(path, "a", encoding="utf-8") as f:
                f.write(rule + "\n")
            reloaded = self._reload_mihomo()
            self._send(200, json.dumps({"ok": True, "message": "规则已添加", "rule": rule, "reloaded": reloaded}).encode(), "application/json; charset=utf-8")
        elif self.path == "/api/update_panel":
            # 触发 MetaCubeXD 面板更新（调面板 POST /upgrade，面板自身写自己的 www）
            try:
                req = urllib.request.Request(PANEL_API + "/upgrade", data=b"", method="POST")
                with urllib.request.urlopen(req, timeout=180) as r:
                    d = json.loads(r.read().decode("utf-8", errors="replace"))
                self._send(200, json.dumps(d).encode(), "application/json; charset=utf-8")
            except Exception as e:
                self._send(200, json.dumps({"ok": False, "message": "更新失败: %s" % e}).encode(), "application/json; charset=utf-8")
        else:
            self._send(404, json.dumps({"ok": False, "message": "not found"}).encode(), "application/json; charset=utf-8")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    httpd = Server(("0.0.0.0", PORT), Handler)
    httpd.serve_forever()
