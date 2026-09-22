#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量 OCR + 校对预览（健壮版）：
- 加 max_tokens 防截断
- 自动重试 2 次（每次换 temperature）
- 三档 JSON 解析：strict → strict=False → 抽取首尾大括号
- 最终仍失败时，把原始内容写到 _ocr_raw.txt 便于人工修复
"""

import os, sys, json, base64, re, time
import urllib.request, urllib.error

# ---- 视觉模型配置（环境变量覆盖） ----
API_BASE = os.environ.get("VISION_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
API_KEY  = os.environ.get("VISION_API_KEY",  "")  # 命令行执行: export VISION_API_KEY=xxx
MODEL    = os.environ.get("VISION_MODEL",    "glm-4v")

# 与 生成讲解课件.py 保持一致 —— 决定输出 JSON 的字段形态
SYSTEM_PROMPT = (
    "你是英语阅读理解题结构化提取助手。"
    "用户会发一张英语阅读题图片（可能含一篇或多篇文章及对应选择题）。"
    "请只输出一个 JSON 对象，不要任何解释、不要 markdown 代码块围栏。"
    "JSON 结构必须如下：\n"
    "{\n"
    '  "passages": [\n'
    "    {\n"
    '      "id": "A",\n'
    '      "text": "<h3>标题</h3><p>正文段落…</p><p>…</p>",\n'
    '      "questions": [\n'
    '        { "q": "1. 题干？", "options": ["A. …","B. …","C. …","D. …"],\n'
    '          "answer": "B",\n'
    '          "explain": "解析：…",\n'
    '          "locate": "原文中答案句的关键片段"\n'
    "        }\n"
    "      ],\n"
    '      "words": ["单词 — 释义", "…"],\n'
    '      "phrases": ["短语 — 释义", "…"],\n'
    '      "points": ["考点1", "考点2"]\n'
    "    }\n"
    "  ]\n"
    "}\n"
    '严格要求：\n'
    '1) 所有字符串里的英文双引号必须写成 \\" ；\n'
    '2) text 必须是合法 HTML，段落用 <p>…</p> 包裹；\n'
    '3) answer 只填一个字母 A/B/C/D；\n'
    '4) locate 必须是原文里真实存在的一小句英文。'
)


def http_post(url, payload, timeout=180):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + API_KEY)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def try_parse_json(text):
    """三档 JSON 解析，返回 dict 或 None。"""
    # 1) 标准
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) 宽松（允许未转义控制字符）
    try:
        return json.decoder.JSONDecoder(strict=False).decode(text)
    except Exception:
        pass
    # 3) 抽取首尾大括号之间的内容再试
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        cand = text[start:end + 1]
        for parser in (json.loads,
                       lambda s: json.decoder.JSONDecoder(strict=False).decode(s)):
            try:
                return parser(cand)
            except Exception:
                continue
    return None


def call_vision(image_b64, max_retries=2):
    """带重试的视觉模型调用。"""
    url = API_BASE.rstrip("/") + "/chat/completions"
    last_content = ""
    for attempt in range(max_retries + 1):
        # 每次重试换 temperature，避免固定模式卡死
        temp = 0.2 + attempt * 0.15
        payload = {
            "model": MODEL,
            "temperature": temp,
            "max_tokens": 2048,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "请提取这张英语阅读题图片，按要求的 JSON 结构返回。"},
                    {"type": "image_url",
                     "image_url": {"url": "data:image/jpeg;base64," + image_b64}},
                ]},
            ],
        }
        try:
            resp = http_post(url, payload)
            content = resp["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2); continue
            raise RuntimeError(f"API 调用失败：{e}")

        last_content = content
        # 去围栏
        content_clean = re.sub(r"^```(?:json)?\s*", "", content.strip())
        content_clean = re.sub(r"\s*```$", "", content_clean)

        parsed = try_parse_json(content_clean)
        if parsed is not None and "passages" in parsed:
            return parsed

        if attempt < max_retries:
            print(f"   JSON 解析失败，第 {attempt+1}/{max_retries} 次重试 "
                  f"(temperature={temp:.2f})...", file=sys.stderr, flush=True)
            time.sleep(2)

    # 全部失败：落盘原始内容
    raw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ocr_raw.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(last_content)
    raise RuntimeError(
        f"JSON 解析失败（已重试 {max_retries} 次）。原始内容已写入 {raw_path}\n"
        f"前 500 字：{last_content[:500]}"
    )


def html_to_text(html: str) -> str:
    html = re.sub(r"</p\s*>", "\n\n", html, flags=re.I)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\n{3,}", "\n\n", html).strip()


def format_proofread(data):
    out = []
    for p in data.get("passages", []):
        out.append("\n" + "=" * 64)
        out.append(f"篇章 {p.get('id', '?')}")
        out.append("=" * 64)
        out.append("\n【原文】")
        out.append(html_to_text(p.get("text", "")))
        out.append("\n【题目 / 选项 / 推断答案】")
        for q in p.get("questions", []):
            out.append("")
            out.append(q["q"])
            for opt in q.get("options", []):
                out.append(f"   {opt}")
            out.append(f"   → 答案: {q.get('answer', '?')}")
            out.append(f"   → 解析: {q.get('explain', '')}")
            loc = q.get("locate", "")
            if loc:
                out.append(f"   → 定位句: {loc}")
        if p.get("words"):
            out.append("\n【重难点单词】")
            for w in p["words"]: out.append(f"   • {w}")
        if p.get("phrases"):
            out.append("\n【重点短语】")
            for x in p["phrases"]: out.append(f"   • {x}")
        if p.get("points"):
            out.append("\n【高频考点】")
            for x in p["points"]: out.append(f"   • {x}")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python ocr_batch.py 图片1 [图片2 ...]")

    combined = {"passages": []}
    for img_path in sys.argv[1:]:
        if not os.path.exists(img_path):
            sys.exit(f"✘ 找不到图片: {img_path}")
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        print(f"→ 正在识别 {os.path.basename(img_path)} ...", file=sys.stderr, flush=True)
        try:
            data = call_vision(b64)
        except RuntimeError as e:
            sys.exit("✘ " + str(e))
        combined["passages"].extend(data.get("passages", []))

    # 按图片出现顺序自动重排篇章 ID 为 A/B/C/D…，支持一次拖多张图
    for i, p in enumerate(combined["passages"]):
        p["id"] = chr(65 + i) if i < 26 else str(i + 1)

    here = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(here, "_ocr_result.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\n✔ 识别完成，共 {len(combined['passages'])} 篇文章", file=sys.stderr)
    print(f"  JSON 已写入 {json_path}", file=sys.stderr)
    print("\n" + "#" * 64)
    print("#  以下是校对稿（请逐字核对）")
    print("#" * 64)
    print(format_proofread(combined))


if __name__ == "__main__":
    main()