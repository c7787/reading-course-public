#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py  —  英语阅读讲解「图片生成器」本地服务（老师图形界面版）

老师只需：
  1) 双击「英语阅读生成器.app」（或 启动生成器.command）
  2) 浏览器自动打开本页 → 选服务商 / 粘贴一次 API Key（可记住）
  3) 把题目图片拖进虚线框（或点选）→ 点「生成讲解课件」
  4) 自动下载并打开「阅读课件_生成.html」去讲课

全程不用终端、不用改名、不用管目录。服务只监听 127.0.0.1（本机），
Key 仅在本机内存/本机配置文件里，不会写进下载的 HTML。
"""

import os
import sys
import json
import datetime
import urllib.parse
import importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8765
PROJ = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJ, "生成器配置.json")

# 动态加载同目录的生成讲解课件.py（文件名含中文，用 importlib 加载）
_spec = importlib.util.spec_from_file_location(
    "genmod", os.path.join(PROJ, "生成讲解课件.py"))
genmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(genmod)

PROVIDERS = {
    "openai":  ("https://api.openai.com/v1", "gpt-4o"),
    "glm":     ("https://open.bigmodel.cn/api/paas/v4", "glm-4v"),
    "qwen":    ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-vl-max"),
    "custom":  ("", ""),
}


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def slog(msg):
    """写到 /tmp/英语阅读生成器.log，便于排查浏览器侧错误是否真的到了服务"""
    try:
        with open("/tmp/英语阅读生成器.log", "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (datetime.datetime.now().strftime("%H:%M:%S"), msg))
    except Exception:
        pass


# ===================== 浏览器界面 HTML（内嵌，无需额外文件） =====================
GUI_HTML = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>英语阅读讲解生成器</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#f6f5ef;color:#2c2c28}
  .wrap{max-width:680px;margin:24px auto;padding:0 18px}
  h1{font-size:22px;color:#2f6f5e;margin:0 0 4px}
  .sub{color:#6b6b63;margin:0 0 18px;font-size:14px}
  .card{background:#fff;border:1px solid #e3e0d6;border-radius:12px;padding:16px 18px;margin-bottom:14px}
  label{font-weight:700;display:block;margin:10px 0 6px;font-size:14px}
  select,input[type=text],input[type=password]{width:100%;padding:9px 11px;border:1px solid #cfccc1;border-radius:8px;font-size:15px}
  .row{display:flex;gap:10px}
  .row>*{flex:1}
  #drop{border:2px dashed #2f6f5e;border-radius:12px;background:#e7f0ec;padding:30px 16px;text-align:center;color:#2f6f5e;cursor:pointer;font-size:15px}
  #drop.hover{background:#d6e8e0}
  #fname{margin-top:8px;color:#6b6b63;font-size:13px;min-height:18px}
  .btn{width:100%;margin-top:14px;background:#2f6f5e;color:#fff;border:none;padding:13px;border-radius:10px;font-size:17px;font-weight:700;cursor:pointer}
  .btn:hover{filter:brightness(1.06)}
  .btn:disabled{opacity:.55;cursor:default}
  #status{margin-top:12px;font-size:14px;min-height:22px;white-space:pre-wrap}
  .ok{color:#2f6f5e}.err{color:#b4452e}
  .tip{font-size:12px;color:#8a877c;margin-top:6px}
  .foot{text-align:center;color:#8a877c;font-size:12px;margin:10px 0 30px}
  a{color:#2f6f5e}
</style></head>
<body>
<div class="wrap">
  <h1>📚 英语阅读讲解生成器</h1>
  <p class="sub">拖入题目图片 → 一键生成可交互讲解网页（高亮 / 定位 / 显答案 / 积累区）</p>

  <div class="card">
    <label>① 选择视觉模型服务商</label>
    <select id="provider">
      <option value="openai">OpenAI（gpt-4o）</option>
      <option value="glm">智谱 GLM（glm-4v）</option>
      <option value="qwen">阿里通义千问（qwen-vl-max）</option>
      <option value="custom">自定义接口</option>
    </select>
    <div class="row">
      <div><label>接口地址 API Base</label><input id="base" type="text" placeholder="https://api.openai.com/v1"></div>
      <div><label>模型名 Model</label><input id="model" type="text" placeholder="gpt-4o"></div>
    </div>
    <label>② API Key（仅本机使用，不会写进课件）</label>
    <input id="key" type="password" placeholder="粘贴你的 API Key">
    <div class="tip"><label style="display:inline;font-weight:400"><input id="remember" type="checkbox"> 记住以上配置（存到本机 生成器配置.json）</label></div>
  </div>

  <div class="card">
    <label>③ 题目图片</label>
    <div id="drop">📷 把题目图片拖到这里，或点击选择图片
      <div id="fname"></div>
    </div>
    <input id="file" type="file" accept="image/*" hidden>
  </div>

  <button class="btn" id="go">生成讲解课件</button>
  <div id="status"></div>
  <p class="foot">本服务仅运行在本机浏览器(localhost)，关闭页面可在底部「退出服务」。</p>
  <div style="text-align:center"><a href="/shutdown">退出本地服务</a></div>
</div>

<script>
const SAVED = __SAVED__;
let file=null;

// 预填已记住的配置
if(SAVED){
  if(SAVED.provider) document.getElementById('provider').value=SAVED.provider;
  if(SAVED.base) document.getElementById('base').value=SAVED.base;
  if(SAVED.model) document.getElementById('model').value=SAVED.model;
  if(SAVED.key) document.getElementById('key').value=SAVED.key;
  if(SAVED.key) document.getElementById('remember').checked=true;
}
function applyProvider(){
  const p=document.getElementById('provider').value;
  const [b,m]=({openai:["https://api.openai.com/v1","gpt-4o"],glm:["https://open.bigmodel.cn/api/paas/v4","glm-4v"],qwen:["https://dashscope.aliyuncs.com/compatible-mode/v1","qwen-vl-max"],custom:["",""]})[p];
  if(!document.getElementById('base').value || p!=='custom') document.getElementById('base').value=b;
  if(!document.getElementById('model').value || p!=='custom') document.getElementById('model').value=m;
}
applyProvider();
document.getElementById('provider').onchange=applyProvider;

const drop=document.getElementById('drop'),fileInput=document.getElementById('file');
drop.onclick=()=>fileInput.click();
fileInput.onchange=e=>{file=e.target.files[0];document.getElementById('fname').textContent=file?('已选择：'+file.name):'';};
['dragover','dragenter'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('hover');}));
['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('hover');}));
drop.addEventListener('drop',e=>{file=e.dataTransfer.files[0];document.getElementById('fname').textContent=file?('已选择：'+file.name):'';});

function setStatus(t,cls){const s=document.getElementById('status');s.textContent=t;s.className=cls||'';}
function download(name,text){
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/html'}));
  a.download=name;a.click();URL.revokeObjectURL(a.href);
}
document.getElementById('go').onclick=async()=>{
  if(!file){alert('请先拖入或选择题目图片');return;}
  const key=document.getElementById('key').value.trim();
  if(!key){alert('请填写 API Key');return;}
  const base=document.getElementById('base').value.trim();
  const model=document.getElementById('model').value.trim();
  const remember=document.getElementById('remember').checked;
  setStatus('⏳ 正在识别题目并生成课件（图片较大时稍慢）…');
  document.getElementById('go').disabled=true;
  try{
    const b64=await new Promise(r=>{const fr=new FileReader();fr.onload=()=>r(fr.result.split(',')[1]);fr.readAsDataURL(file);});
    const res=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({image_b64:b64,api_base:base,api_key:key,model,remember})});
    const t=await res.text();
    let j; try{j=JSON.parse(t);}catch(parseErr){
      // 响应不是 JSON：通常是被浏览器代理/插件拦截后返回了 HTML/空
      setStatus('✘ 服务返回的不是 JSON（很可能被本机代理或浏览器插件拦截）。\nHTTP '+res.status+(res.statusText?' '+res.statusText:'')+'\n返回内容前 400 字：\n'+(t||'(空)').slice(0,400),'err');
      return;
    }
    if(j.error){setStatus('✘ '+j.error,'err');return;}
    download('阅读课件_生成.html',j.html);
    window.open(URL.createObjectURL(new Blob([j.html],{type:'text/html'})),'_blank');
    setStatus('✔ 已生成！已自动下载「阅读课件_生成.html」并在新标签页打开。','ok');
  }catch(e){setStatus('✘ 网络或生成出错：'+(e.message||e),'err');}
  finally{document.getElementById('go').disabled=false;}
};
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            saved = load_config()
            page = GUI_HTML.replace("__SAVED__", json.dumps(saved, ensure_ascii=False))
            self._send(200, page, "text/html; charset=utf-8")
        elif self.path == "/shutdown":
            self._send(200, "<h2>本地服务已退出，可关闭此页。</h2>")
            # 延迟退出，确保响应先发出
            import threading
            threading.Timer(0.3, lambda: os._exit(0)).start()
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/generate":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
        except Exception as e:
            slog("POST /api/generate 读取请求体失败: %s" % e)
            self._send(400, json.dumps({"error": "请求格式错误：" + str(e)}))
            return
        slog("POST /api/generate, body bytes=%d, ua=%s" % (length, self.headers.get("User-Agent", "")[:60]))
        try:
            payload = json.loads(body)
            passages = genmod.vision_to_passages(
                payload["image_b64"], payload["api_base"], payload["api_key"], payload["model"])
            html = genmod.render_filled_template(passages)
            if payload.get("remember"):
                save_config({
                    "provider": payload.get("provider", ""),
                    "base": payload["api_base"], "model": payload["model"], "key": payload["api_key"]
                })
            slog("POST /api/generate ✔ 成功，html=%d 字节" % len(html))
            self._send(200, json.dumps({"html": html}, ensure_ascii=False))
        except RuntimeError as e:
            slog("POST /api/generate RuntimeError: %s" % e)
            self._send(400, json.dumps({"error": str(e)}))
        except Exception as e:
            slog("POST /api/generate Exception: %s" % e)
            self._send(500, json.dumps({"error": "生成失败：" + str(e)}))

    def log_message(self, *a):
        pass  # 静默日志，避免刷屏


def main():
    # 端口被占用则提示已在运行
    try:
        srv = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print("✘ 端口 %d 被占用，生成器可能已在运行，请直接打开 http://127.0.0.1:%d/" % (PORT, PORT))
        sys.exit(1)
    print("✔ 英语阅读生成器已启动：http://127.0.0.1:%d/  （关闭请访问该页底部「退出本地服务」）" % PORT)
    srv.serve_forever()


if __name__ == "__main__":
    main()
