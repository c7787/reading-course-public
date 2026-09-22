#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel 入口：把 webapp/app.py 的 FastAPI app 暴露给 Vercel 的 @vercel/python 构建器。
部署在项目根目录运行 `vercel` 即可。
"""
import sys
from pathlib import Path

# 把 webapp/ 加进 sys.path，这样 app.py 能找到同级目录的 static/ 等
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402  (webapp/app.py)