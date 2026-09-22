#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成讲解课件.py  —  把英语阅读题图片自动变成可交互讲解 HTML

本文件既是命令行工具，也是网页生成器(server.py) 复用的大脑：
  - 命令行用法：
      python 生成讲解课件.py 题目.jpg [--api-base URL] [--api-key KEY] [--model M]
      python 生成讲解课件.py --demo        # 不联网自测
  - 网页用法：由 server.py 调用本模块的 vision_to_passages / render_filled_template

视觉接口（OpenAI 兼容格式）：OpenAI gpt-4o / 智谱 glm-4v / 阿里 qwen-vl-max 等。
注意：DeepSeek 官方 chat 不支持看图，请勿使用。
"""

import os
import re
import sys
import json
import base64
import datetime
import urllib.request
import urllib.error

# ===================== 配置区（可用环境变量 / 命令行覆盖） =====================
API_BASE = os.environ.get("VISION_API_BASE", "https://api.openai.com/v1")
API_KEY  = os.environ.get("VISION_API_KEY", "")
MODEL    = os.environ.get("VISION_MODEL", "gpt-4o")

TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "阅读课件.html")
OUT_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "阅读课件_生成.html")

START_MARK = "/* ===PASSAGES_START=== */"
END_MARK   = "/* ===PASSAGES_END=== */"

# ===================== 让模型返回的结构化提示词 =====================
SYSTEM_PROMPT = (
    "你是英语阅读理解题结构化提取助手。"
    "用户会发一张英语阅读题图片（可能含一篇或多篇文章及对应选择题）。"
    "请只输出一个 JSON 对象，不要任何解释、不要 markdown 代码块围栏。"
    "JSON 结构必须如下：\n"
    "{\n"
    '  "passages": [\n'
    "    {\n"
    '      "id": "A",                       // 篇章标签，按图片出现顺序用 A/B/C/D\n'
    '      "text": "<h3>标题</h3><p>正文段落…</p><p>…</p>",  // 原文 HTML，段落用 <p> 包裹，重点词可用 <b>\n'
    '      "questions": [\n'
    '        { "q": "1. 题干？", "options": ["A. …","B. …","C. …","D. …"],\n'
    '          "answer": "B",                // 正确选项字母\n'
    '          "explain": "解析：…",          // 答案解析\n'
    '          "locate": "原文中答案句的关键片段" // 用于「定位原文」高亮，留空字符串则无定位\n'
    "        }\n"
    "      ],\n"
    '      "words": ["单词 — 释义", "…"],      // 重难点单词，每行一条\n'
    '      "phrases": ["短语 — 释义", "…"],    // 重点短语\n'
    '      "points": ["考点1", "考点2"],       // 高频考点\n'
    '      "techniques": ["技巧1", "技巧2"]    // 考试做题技巧（应试策略/解题方法），针对该篇体裁，3-6 条\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "要求：answer 只填字母；locate 必须是原文里真实存在的一小句英文；"
    "trans 为分句中文翻译，必须是与 text 的 <p> 段落数量、顺序一一对应的 HTML（每段用 <p> 包裹）；"
    "sentences 为逐句精读数据，数组，每项为 {\"en\":原句英文,\"zh\":中文翻译,\"analysis\":语法结构拆解}，按原文句子顺序；"
    "text 必须是合法 HTML（含 <p> 标签），不要使用 markdown。"
)

# ===================== 模板里没被图片覆盖时的留白占位 =====================
def blank_passage(label):
    return {
        "text": "<h3>%s 篇 ·（在此替换为你的真题标题）</h3><p>（在此粘贴 %s 篇阅读原文，或运行生成器自动填充。）</p>" % (label, label),
        "trans": "<p>（在此填写对应中文翻译）</p>",
        "sentences": [],
        "questions": [{
            "q": "1. （在此填写题干）",
            "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
            "answer": "B",
            "explain": "（在此填写解析）",
            "locate": ""
        }],
        "words": ["（在此填写重难点单词，每行一条）"],
        "phrases": ["（在此填写重点短语，每行一条）"],
        "points": ["（在此填写高频考点，每行一条）"],
        "techniques": ["（在此填写做题技巧，如：先读题干再回原文定位、关注同义替换、排除绝对化选项等）"]
    }

FALLBACK = {k: blank_passage(k) for k in "ABCD"}


# ===================== 调用视觉大模型（出错抛 RuntimeError，不退出进程） =====================
def call_vision(image_b64, api_base, api_key, model):
    if not api_key:
        raise RuntimeError("未配置 API key。请在界面填写，或用环境变量 VISION_API_KEY。")
    url = api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "请提取这张英语阅读题图片，按要求的 JSON 结构返回。"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}}
            ]}
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + api_key)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            out = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("API 请求失败 %s：%s" % (e.code, e.read().decode("utf-8", "ignore")[:400]))
    except Exception as e:
        raise RuntimeError("调用出错：%s" % e)
    content = out["choices"][0]["message"]["content"]
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())   # 去掉 ```json 围栏
    content = re.sub(r"\s*```$", "", content.strip())
    try:
        return json.loads(content)
    except Exception:
        raise RuntimeError("模型返回的不是合法 JSON，请检查模型或重试。\n返回内容前 300 字：\n%s" % content[:300])


# ===================== 结构化数据 → PASSAGES（图片覆盖的篇章用图片，其余留白） =====================
def build_passages(model_data):
    model_map = {}
    for p in model_data.get("passages", []):
        pid = str(p.get("id", "A")).upper()
        if pid not in "ABCD":
            pid = "A"
        item = {k: v for k, v in p.items() if k != "id"}
        model_map[pid] = item
    return {k: model_map.get(k, FALLBACK[k]) for k in "ABCD"}


def vision_to_passages(image_b64, api_base, api_key, model):
    """图片 base64 → PASSAGES 字典（供 server.py 调用）"""
    return build_passages(call_vision(image_b64, api_base, api_key, model))


# ===================== 把 PASSAGES 注入模板，返回完整 HTML 字符串 =====================
def _sanitize(obj):
    """递归清洗：把 JSON 不允许 / <script> 会崩的控制字符替换掉。
    - U+2028 / U+2029：json.dumps 默认不转义，但会破坏 <script> 字符串，统一换成换行
    - 其余控制字符（\r \t 等）换成空格，避免意外
    """
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, str):
        obj = obj.replace("\u2028", "\n").replace("\u2029", "\n")
        return "".join(ch if (ch >= " " or ch == "\n") else " " for ch in obj)
    return obj


def render_filled_template(passages):
    if not os.path.exists(TEMPLATE_FILE):
        raise RuntimeError("找不到模板文件：%s（请与本脚本放同一目录）" % TEMPLATE_FILE)
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    passages = _sanitize(passages)
    block = "%s\nconst PASSAGES = %s;\n%s" % (
        START_MARK,
        json.dumps(passages, ensure_ascii=False, indent=2),
        END_MARK
    )
    # 注意：re.sub 会把替换串里的 \n \" \\ 当作转义处理，破坏 JSON 字符串值。
    # 必须用 lambda 返回 block，re 才会原样插入、不做转义解释。
    new_html, n = re.subn(
        re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
        lambda m: block, html, count=1, flags=re.S
    )
    if n == 0:
        raise RuntimeError("未在模板中找到 PASSAGES 标记，模板可能被改动。")
    return new_html


def inject_into_template(passages):
    out = render_filled_template(passages)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(out)
    return OUT_FILE


# ===================== 内置示例（--demo 自测用） =====================
def demo_data():
    return {"passages": [{
        "id": "A",
        "text": "<h3>Demo: A Friendly Robot</h3><p>A new robot called <b>Helper</b> can carry books and water plants at school. Students love it.</p><p>It works for 6 hours a day and saves teachers' time.</p>",
        "questions": [
            {"q": "1. What can the robot do?", "options": ["A. Cook meals", "B. Carry books", "C. Drive cars", "D. Teach class"], "answer": "B", "explain": "原文 A new robot ... can carry books。", "locate": "can carry books"},
            {"q": "2. How long does it work a day?", "options": ["A. 2 hours", "B. 4 hours", "C. 6 hours", "D. 8 hours"], "answer": "C", "explain": "原文 It works for 6 hours a day。", "locate": "works for 6 hours a day"}
        ],
        "words": ["robot — 机器人", "carry — 搬运", "plant — 植物"],
        "phrases": ["save time — 节省时间", "at school — 在学校"],
        "points": ["细节定位题", "数字识别题"]
    }]}


# ===================== 入口（命令行） =====================
def main():
    args = sys.argv[1:]
    if "--demo" in args:
        print("· 自测模式：使用内置示例，不调用网络。")
        data = demo_data()
    else:
        if not args or not args[0].lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")):
            sys.exit("用法：python 生成讲解课件.py 题目.jpg [--api-base URL] [--api-key KEY] [--model MODEL]\n"
                     "      或：python 生成讲解课件.py --demo")
        img_path = args[0]
        if not os.path.exists(img_path):
            sys.exit("✘ 图片不存在：%s" % img_path)
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        api_base, api_key, model = API_BASE, API_KEY, MODEL
        for i, a in enumerate(args[1:]):
            if a == "--api-base": api_base = args[i + 2]
            elif a == "--api-key": api_key = args[i + 2]
            elif a == "--model": model = args[i + 2]
        print("· 正在调用视觉模型提取题目（%s）…" % model)
        try:
            data = call_vision(b64, api_base, api_key, model)
        except RuntimeError as e:
            sys.exit("✘ " + str(e))

    try:
        passages = build_passages(data)
        out = inject_into_template(passages)
    except RuntimeError as e:
        sys.exit("✘ " + str(e))
    print("✔ 已生成：%s" % out)
    print("  覆盖篇章：%s" % (",".join(k for k in "ABCD" if passages[k] is not FALLBACK[k]) or "（无，仅留白）"))
    print("  双击该文件即可在浏览器打开讲课。")


if __name__ == "__main__":
    main()
