#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建「扫码体验」海报：把二维码 SVG 内联进自包含 HTML（A4 竖版，可打印）。
    python3 marketing/build_poster.py                # 用占位二维码
    python3 marketing/build_poster.py reading-qr.svg # 用真实部署后的二维码
输出：marketing/扫码体验海报.html
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_QR = HERE / "_qr_placeholder.svg"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>英语阅读互动课件生成器 · 扫码体验</title>
<style>
  :root{
    --teal:#15616d; --teal-d:#0e4651; --amber:#f0a23b; --bg:#f6f3ee;
    --ink:#20323a; --muted:#5d6f76; --card:#ffffff;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
       color:var(--ink);background:var(--bg);}
  .page{width:720px;margin:0 auto;padding:36px 40px 30px;background:var(--bg);}
  .hero{background:linear-gradient(135deg,var(--teal),var(--teal-d));
        color:#fff;border-radius:20px;padding:26px 30px;box-shadow:0 10px 30px rgba(21,97,109,.25);}
  .hero h1{margin:0;font-size:30px;letter-spacing:1px;}
  .hero .sub{margin-top:8px;font-size:16px;opacity:.92;}
  .chips{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;}
  .chip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);
        color:#fff;font-size:13px;padding:6px 12px;border-radius:999px;}
  .props{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:22px 0;}
  .pcard{background:var(--card);border-radius:14px;padding:16px 18px;
         box-shadow:0 4px 14px rgba(32,50,58,.08);border:1px solid #ece7df;}
  .pcard .ic{font-size:24px;}
  .pcard .t{font-weight:700;font-size:16px;margin:6px 0 4px;color:var(--teal);}
  .pcard .d{font-size:13px;color:var(--muted);line-height:1.6;}
  .qrwrap{margin:8px 0 4px;text-align:center;
          background:linear-gradient(135deg,#fff,#fbf7f1);
          border:2px dashed var(--amber);border-radius:18px;padding:22px;}
  .qrwrap h2{margin:0 0 4px;color:var(--teal);font-size:22px;}
  .qrwrap .tip{color:var(--muted);font-size:13px;margin-bottom:14px;}
  .qr{display:inline-block;background:#fff;padding:12px;border-radius:14px;
      box-shadow:0 6px 18px rgba(32,50,58,.12);}
  .qr svg{width:240px;height:240px;display:block;}
  .scan{margin-top:10px;font-size:14px;color:var(--ink);}
  .scan b{color:var(--amber);}
  .foot{margin-top:18px;text-align:center;font-size:13px;color:var(--muted);line-height:1.7;}
  .note{margin-top:10px;font-size:12px;color:#a08a5d;text-align:center;}
  @media print{
    @page{size:A4;margin:10mm;}
    body{background:#fff;}
    .page{width:100%;margin:0;padding:0 6mm;}
    .hero{box-shadow:none;}
  }
</style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <h1>📚 英语阅读互动课件生成器</h1>
      <div class="sub">拍张题图，30 秒生成「可讲解」的英语阅读课件</div>
      <div class="chips">
        <span class="chip">免注册</span>
        <span class="chip">前 3 次免费</span>
        <span class="chip">课件可编辑</span>
        <span class="chip">一键打印 / 导出 PDF</span>
      </div>
    </div>

    <div class="props">
      <div class="pcard"><div class="ic">📷</div><div class="t">拍图即出</div>
        <div class="d">试卷 / 教辅 / 电子稿，手机拍一张阅读题，自动解析出原文与题目。</div></div>
      <div class="pcard"><div class="ic">📖</div><div class="t">逐句精读</div>
        <div class="d">点任一句弹出翻译 + 语法拆解，课堂随时讲透长难句。</div></div>
      <div class="pcard"><div class="ic">✅</div><div class="t">点选判对错</div>
        <div class="d">学生自测不预弹答案；错题自动定位原文，教师模式一键讲。</div></div>
      <div class="pcard"><div class="ic">🖨️</div><div class="t">打印 / 导出</div>
        <div class="d">重难点单词、短语、考点、做题技巧自动积累，学生版 / 教师版双模式。</div></div>
    </div>

    <div class="qrwrap">
      <h2>扫码免费体验</h2>
      <div class="tip">把下面二维码放到公众号 / 朋友圈 / 教师群</div>
      <div class="qr">__QR_SVG__</div>
      <div class="scan">手机相机对准二维码 <b>扫一扫</b>，即刻使用</div>
    </div>

    <div class="note">※ 本二维码为占位图，部署上线后用 marketing/make_qr.py 生成真实二维码并重新 build 即可替换。</div>

    <div class="foot">
      教师专属 · 课件可编辑可打印 · 反馈 / 加群请扫码后联系<br>
      © 2026 陈万里（揭阳） · 英语阅读互动课件生成器
    </div>
  </div>
</body>
</html>
"""

def main():
    qr_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_QR
    if not qr_path.exists():
        qr_path = DEFAULT_QR
    qr_svg = qr_path.read_text(encoding="utf-8")
    html = TEMPLATE.replace("__QR_SVG__", qr_svg)
    out = HERE / "扫码体验海报.html"
    out.write_text(html, encoding="utf-8")
    print(f"已生成海报：{out}")
    print(f"二维码来源：{qr_path}")

if __name__ == "__main__":
    main()
