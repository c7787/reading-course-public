#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _ocr_result.json 注入阅读课件.html 模板，生成阅读课件_生成.html。"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from 生成讲解课件 import build_passages, inject_into_template  # noqa: E402

with open(os.path.join(HERE, "_ocr_result.json"), "r", encoding="utf-8") as f:
    model_data = json.load(f)

passages = build_passages(model_data)
out = inject_into_template(passages)
print("✔ 已生成:", out)
print("   覆盖篇章:", ",".join(k for k in "ABCD") or "（无）")
print("   A/B 来自图片，C/D 为模板留白。")
