#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webapp/app.py — 公开版「英语阅读互动课件生成器」FastAPI 后端
- 复用项目根目录的 生成讲解课件.py（不复制代码，单一事实源）
- 环境变量: VISION_API_KEY (必填), VISION_API_BASE, VISION_MODEL
- 部署: Vercel / 阿里云函数计算 / Docker / VPS 通用
"""
import os, sys, time, base64, hashlib
from pathlib import Path
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parent.parent  # 教学工具/
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from 生成讲解课件 import call_vision, build_passages, render_filled_template

# ===================== 配置（环境变量覆盖） =====================
API_BASE = os.environ.get("VISION_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
API_KEY  = os.environ.get("VISION_API_KEY", "")
MODEL    = os.environ.get("VISION_MODEL", "glm-4v")

MAX_FILES        = int(os.environ.get("MAX_FILES", "8"))
MAX_FILE_BYTES   = int(os.environ.get("MAX_FILE_BYTES", str(10 * 1024 * 1024)))  # 10MB
DAILY_IP_LIMIT   = int(os.environ.get("DAILY_IP_LIMIT", "30"))  # 软上限（防脚本刷）
FREE_TIER_LIMIT  = int(os.environ.get("FREE_TIER_LIMIT", "3"))   # 客户端免费次数（前端也会用）

STATIC_DIR    = Path(__file__).resolve().parent / "static"
# serverless 环境（Vercel / 阿里云 FC / 腾讯云等）文件系统只读（除 /tmp/），
# 下载目录优先用 static/downloads，写不进去时退到 /tmp/（自适应，不依赖特定环境变量）
DOWNLOADS_DIR = STATIC_DIR / "downloads"
if not DOWNLOADS_DIR.is_dir():
    try:
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
try:
    _t = DOWNLOADS_DIR / ".writetest"
    _t.write_text("1"); _t.unlink()
except (OSError, PermissionError):
    DOWNLOADS_DIR = Path("/tmp/webapp-downloads")
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="英语阅读互动课件生成器", version="1.0")

# ===================== 内存级 IP 速率限制（best-effort；服务器下每次冷启动会重置，仅作软上限） =====================
_ip_window = defaultdict(lambda: deque())

def client_ip(req: Request) -> str:
    xff = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
    if xff:
        return xff.split(",")[0].strip()
    return req.client.host if req.client else "unknown"

def rate_ok(ip: str) -> tuple[bool, int]:
    now = time.time()
    dq = _ip_window[ip]
    while dq and now - dq[0] > 86400:
        dq.popleft()
    if len(dq) >= DAILY_IP_LIMIT:
        return False, 0
    dq.append(now)
    return True, DAILY_IP_LIMIT - len(dq)

# ===================== 路由 =====================
@app.get("/health")
def health():
    return {"ok": True, "has_api_key": bool(API_KEY), "model": MODEL,
            "free_tier": FREE_TIER_LIMIT, "daily_ip_limit": DAILY_IP_LIMIT}

@app.get("/", response_class=HTMLResponse)
def index():
    p = STATIC_DIR / "index.html"
    if not p.exists():
        return HTMLResponse("<h1>index.html missing</h1>", status_code=500)
    return FileResponse(str(p))

@app.get("/sample", response_class=HTMLResponse)
def sample():
    p = STATIC_DIR / "sample.html"
    if not p.exists():
        raise HTTPException(404, "示例未生成。运行 webapp/make_sample.py 构建。")
    return FileResponse(str(p))

@app.post("/api/generate")
async def generate(request: Request, files: list[UploadFile] = File(...)):
    ip = client_ip(request)
    ok, remaining = rate_ok(ip)
    if not ok:
        raise HTTPException(429, f"今日体验已达上限（{DAILY_IP_LIMIT}次/天/IP），明天再来。")

    if not API_KEY:
        raise HTTPException(503, "服务端未配置 VISION_API_KEY，无法生成。请联系管理员。")
    if not files:
        raise HTTPException(400, "请上传至少一张阅读题图片。")
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"一次最多 {MAX_FILES} 张图。")

    # 读图
    images_b64 = []
    for f in files[:MAX_FILES]:
        b = await f.read()
        if len(b) > MAX_FILE_BYTES:
            raise HTTPException(400, f"{f.filename or '图片'} 超过 {MAX_FILE_BYTES//1024//1024}MB，请压缩后重试。")
        images_b64.append(base64.b64encode(b).decode("ascii"))

    # 逐张 OCR + 按出现顺序重排 A/B/C/D
    all_passages = []
    errs = []
    for idx, b64 in enumerate(images_b64):
        try:
            data = call_vision(b64, API_BASE, API_KEY, MODEL)
        except Exception as e:
            errs.append(f"第{idx+1}张图识别失败：{e}")
            continue
        for p in data.get("passages", []):
            p2 = dict(p)
            p2["id"] = chr(65 + len(all_passages)) if len(all_passages) < 26 else str(len(all_passages) + 1)
            all_passages.append(p2)
        if idx < len(images_b64) - 1:
            time.sleep(0.3)  # 礼貌限速

    if not all_passages:
        detail = ("；".join(errs) + "；") if errs else ""
        raise HTTPException(400, detail + "未从图片中识别到任何阅读题，请检查图片是否清晰、含题目。")

    passages = build_passages({"passages": all_passages})
    try:
        html = render_filled_template(passages)
    except Exception as e:
        raise HTTPException(500, f"渲染课件失败：{e}")

    # 落盘供下载/预览
    now = int(time.time())
    digest = hashlib.md5(html.encode()).hexdigest()[:8]
    fname = f"reading_{now}_{digest}.html"
    (DOWNLOADS_DIR / fname).write_text(html, encoding="utf-8")

    return {
        "ok": True,
        "filename": fname,
        "passages": list(passages.keys()),
        "questions_total": sum(len(passages[k].get("questions", [])) for k in passages),
        "download_url": f"/download/{fname}",
        "preview_url": f"/preview/{fname}",
        "ip_remaining": remaining,
        "free_tier_limit": FREE_TIER_LIMIT,
        "warnings": errs,
    }

@app.get("/download/{fname}")
def download(fname: str):
    if ".." in fname or "/" in fname or "\\" in fname:
        raise HTTPException(404)
    p = DOWNLOADS_DIR / fname
    if not p.exists():
        raise HTTPException(404, "文件已过期，请重新生成。")
    return FileResponse(str(p), filename="英语阅读互动课件.html", media_type="text/html")

@app.get("/preview/{fname}")
def preview(fname: str):
    if ".." in fname or "/" in fname or "\\" in fname:
        raise HTTPException(404)
    p = DOWNLOADS_DIR / fname
    if not p.exists():
        raise HTTPException(404)
    return HTMLResponse(p.read_text(encoding="utf-8"))

# 兜底：未匹配路径返回首页（SPA 友好，但这里主要是 API + 静态）
@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "not found"}, status_code=404)
    return FileResponse(str(STATIC_DIR / "index.html"))