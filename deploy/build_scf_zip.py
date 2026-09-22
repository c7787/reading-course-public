#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建腾讯云 SCF 部署包 zip（确定性、UTF-8 安全，避免 macOS zip 漏掉中文文件名）。
用法：python3 deploy/build_scf_zip.py
产出：项目根目录/reading-course-scf.zip（zip 根 = 项目根，含 webapp/ + 生成讲解课件.py）
"""
import os
import zipfile
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "reading-course-scf.zip"

# 排除的目录
EXCLUDE_DIRS = {".git", "__pycache__", ".workbuddy-ai", ".venv", "node_modules"}
# 排除的文件
EXCLUDE_FILES = {".env", ".DS_Store", "reading-course-scf.zip", "_ocr_result.json", "阅读课件_生成.html"}


def excluded(p: pathlib.Path) -> bool:
    rel = p.relative_to(ROOT)
    parts = rel.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if "__pycache__" in parts:
        return True
    if p.name in EXCLUDE_FILES:
        return True
    return False


def main():
    if OUT.exists():
        OUT.unlink()
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob("*")):
            if p.is_file() and not excluded(p):
                arcname = p.relative_to(ROOT).as_posix()
                z.write(p, arcname)
                count += 1
    print(f"已写入 {OUT}（{OUT.stat().st_size} 字节，{count} 个文件）")


if __name__ == "__main__":
    main()
