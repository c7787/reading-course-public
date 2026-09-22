#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 _ocr_result.json 中每篇的原文每段生成中文翻译，写入 trans 字段。
trans 为与 text 的 <p> 段一一对应的 HTML：<p>中文段</p><p>中文段</p>...
key 从环境变量 VISION_API_KEY 读取（不落盘）。
"""
import os, sys, json, re, time, urllib.request, urllib.error

API_BASE = os.environ.get("VISION_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
API_KEY  = os.environ.get("VISION_API_KEY", "")
MODEL    = os.environ.get("VISION_MODEL", "glm-4v")
HERE = os.path.dirname(os.path.abspath(__file__))


def post(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_BASE.rstrip("/") + "/chat/completions",
                                 data=data, method="POST")
    req.add_header("Authorization", "Bearer " + API_KEY)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]


def parse_json(text):
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return json.decoder.JSONDecoder(strict=False).decode(text)
    except Exception:
        pass
    a, b = text.find("["), text.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(text[a:b + 1])
        except Exception:
            pass
    return None


def translate(paras, max_retries=2):
    numbered = "\n".join(f"{i+1}. {p}" for i, p in enumerate(paras))
    prompt = ("请将以下英语段落逐段翻译成中文，保持段落数量与顺序完全一致。"
              "只返回一个 JSON 数组，每个元素是一段的中文译文，不要任何解释、不要 markdown 围栏。\n\n"
              + numbered)
    for attempt in range(max_retries + 1):
        try:
            content = post({
                "model": MODEL, "temperature": 0.2, "max_tokens": 2048,
                "messages": [
                    {"role": "system", "content": "你是严谨的英译中翻译助手，译文准确、通顺、符合中学英语课堂用语。"},
                    {"role": "user", "content": prompt},
                ],
            })
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2); continue
            raise RuntimeError(f"翻译 API 出错：{e}")
        res = parse_json(content)
        if isinstance(res, list):
            return res
        if attempt < max_retries:
            time.sleep(2); continue
    raise RuntimeError("翻译结果不是合法 JSON 数组：" + str(content)[:300])


def extract_paras(text):
    return re.findall(r"<p[^>]*>(.*?)</p>", text, re.S | re.I)


def main():
    if not API_KEY:
        sys.exit("未设置 VISION_API_KEY 环境变量")
    path = os.path.join(HERE, "_ocr_result.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    for p in data["passages"]:
        paras = extract_paras(p.get("text", ""))
        clean = [re.sub(r"<[^>]+>", "", x).strip() for x in paras]
        clean = [x for x in clean if x]
        if not clean:
            continue
        print(f"→ 翻译篇章 {p.get('id')}（{len(clean)} 段）...", file=sys.stderr, flush=True)
        try:
            zh = translate(clean)
        except RuntimeError as e:
            print("  ✘ " + str(e), file=sys.stderr); continue
        if len(zh) != len(clean):
            print(f"  ⚠ 段数不一致（模型 {len(zh)} / 原文 {len(clean)}），按原文段数对齐", file=sys.stderr)
            zh = (zh + [""] * len(clean))[:len(clean)]
        p["trans"] = "".join(f"<p>{z}</p>" for z in zh)
        changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✔ 分句翻译已写入 _ocr_result.json 的 trans 字段", file=sys.stderr)
    else:
        print("未作改动", file=sys.stderr)


if __name__ == "__main__":
    main()