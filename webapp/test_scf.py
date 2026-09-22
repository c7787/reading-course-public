#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 mock 的 API 网关事件验证 webapp/scf_main.main_handler。
跑：python3 webapp/test_scf.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from webapp.scf_main import main_handler

def mock_get(path="/health", headers=None):
    return {
        "httpMethod": "GET",
        "path": path,
        "headers": headers or {},
        "body": "",
        "isBase64Encoded": False,
        "queryStringParameters": {},
    }

def mock_post(path="/api/generate", headers=None, body="", is_b64=False):
    return {
        "httpMethod": "POST",
        "path": path,
        "headers": headers or {"Content-Type": "application/json"},
        "body": body,
        "isBase64Encoded": is_b64,
        "queryStringParameters": {},
    }

def show(label, resp):
    body_preview = resp["body"][:120].replace("\n", "\\n") if isinstance(resp.get("body"), str) else "(non-str)"
    print(f"{label}: status={resp['statusCode']} "
          f"isB64={resp['isBase64Encoded']} "
          f"ct={resp['headers'].get('Content-Type','?')[:40]} "
          f"body_len={len(resp['body']) if isinstance(resp['body'],str) else '?'} "
          f"preview={body_preview!r}")

# 1. GET /health
show("GET /health    ", main_handler(mock_get("/health"), None))
# 2. GET /
show("GET /          ", main_handler(mock_get("/"), None))
# 3. GET /sample
show("GET /sample    ", main_handler(mock_get("/sample"), None))
# 4. GET /random-page  → 404 兜底（首页）
show("GET /random    ", main_handler(mock_get("/random"), None))
# 5. POST /api/generate (无文件) → 422
show("POST /api/generate(无文件)", main_handler(mock_post("/api/generate"), None))
# 6. POST /api/generate (无 key + multipart) → 503
mp_body = '--xxx\r\nContent-Disposition: form-data; name="files"; filename="a.png"\r\n\r\nbinary\r\n--xxx--\r\n'
show("POST /api/generate(无key)", main_handler(
    mock_post("/api/generate",
              headers={"Content-Type": "multipart/form-data; boundary=xxx"},
              body=mp_body), None))
# 7. GET /api/notfound → JSON 404
show("GET /api/notfnd", main_handler(mock_get("/api/notfound"), None))