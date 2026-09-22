#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 SCF（独立云函数）入口：把 webapp/app.py 的 FastAPI ASGI app 包装为
API 网关触发器用的同步 handler。

部署方式（控制台"通过代码包创建"）：
    1. 把整个项目根目录打成 zip（必须含 webapp/ + 生成讲解课件.py）
    2. 上传 zip，运行环境选 Python 3.10
    3. 执行方法（Handler）填：
           webapp.scf_main.main_handler
    4. 触发管理 → 新建触发 → 选「API 网关触发」
    5. 配置 API（路径 / 方法 任意），保存后拿到 https://service-xxx.apigw.tencentcs.com/release/
    6. 触发器「启用」后访问 /health 验证 has_api_key:true
    7. 环境变量加 VISION_API_KEY=你的智谱key
"""
import asyncio
import base64
import json

from webapp.app import app  # FastAPI ASGI app（单一事实源，不复制代码）


def _build_scope_and_state(event):
    """把 API 网关事件转成 ASGI scope + receive/send + 收集响应。"""
    method = (event.get("httpMethod") or "GET").upper()
    path = event.get("path") or "/"

    # query string
    qs = event.get("queryString")
    if qs is None or qs == "":
        params = event.get("queryStringParameters") or {}
        if params:
            from urllib.parse import urlencode
            qs = urlencode(params)
        else:
            qs = ""

    # headers：API 网关的 headers 是 dict，可能大小写都有，统一小写
    src_headers = event.get("headers") or {}
    hmap = {}
    for k, v in src_headers.items():
        if k is None:
            continue
        kl = k.lower()
        if kl not in hmap:  # 去重，保留首个
            hmap[kl] = v if isinstance(v, str) else str(v)
    headers_list = [[k.encode("utf-8"), v.encode("utf-8")] for k, v in hmap.items()]

    # body
    body_str = event.get("body") or ""
    is_b64 = bool(event.get("isBase64Encoded"))
    if is_b64 and body_str:
        body_bytes = base64.b64decode(body_str)
    else:
        body_bytes = body_str.encode("utf-8") if isinstance(body_str, str) else (body_str or b"")

    # scheme：API 网关外层是 https
    scheme = "https"

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": scheme,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": qs.encode("utf-8") if isinstance(qs, str) else (qs or b""),
        "root_path": "",
        "headers": headers_list,
        "server": ("scf.apigw.tencentcs.com", 443),
        "client": ("127.0.0.1", 0),
    }

    state = {"status": 200, "headers": [], "chunks": []}

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            state["status"] = msg.get("status", 200)
            state["headers"] = msg.get("headers", []) or []
        elif msg["type"] == "http.response.body":
            state["chunks"].append(msg.get("body", b"") or b"")

    return scope, receive, send, state


def _run_asgi_sync(event: dict) -> dict:
    """同步跑 FastAPI ASGI app，返回 API 网关格式响应。"""
    scope, receive, send, state = _build_scope_and_state(event)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(app(scope, receive, send))
    finally:
        loop.close()

    body_out = b"".join(state["chunks"])
    resp_headers = {}
    for k, v in state["headers"]:
        ks = k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else str(k)
        vs = v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else str(v)
        if ks.lower() not in resp_headers:
            resp_headers[ks] = vs

    ct = resp_headers.get("Content-Type") or resp_headers.get("content-type") or "application/octet-stream"
    is_text = isinstance(ct, str) and (
        ct.startswith("text/")
        or "json" in ct
        or "javascript" in ct
        or "xml" in ct
        or ct.startswith("application/x-www-form-urlencoded")
    )

    if is_text:
        body_str_out = body_out.decode("utf-8", errors="replace")
        is_b64_out = False
    else:
        body_str_out = base64.b64encode(body_out).decode("ascii")
        is_b64_out = True

    return {
        "isBase64Encoded": is_b64_out,
        "statusCode": state["status"],
        "headers": resp_headers,
        "body": body_str_out,
    }


def main_handler(event, context):
    """SCF API 网关入口函数（同步）。

    在 SCF 控制台「执行方法」字段填 webapp.syntax.scf_main.main_handler。
    """
    try:
        if not isinstance(event, dict):
            raise ValueError("event 必须是 dict")
        return _run_asgi_sync(event)
    except Exception as e:
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps({"detail": "server error", "error": str(e)}, ensure_ascii=False),
        }