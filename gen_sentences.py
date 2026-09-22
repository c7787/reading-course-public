#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 _ocr_result.json 中每篇生成「逐句精读」数据，写入 sentences 字段：
[ {"en":原句, "zh":翻译, "analysis":结构拆解}, ... ]
key 从环境变量 VISION_API_KEY 读取（不落盘）。
"""
import os, sys, json, re, time, urllib.request, urllib.error

API_BASE = os.environ.get("VISION_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
API_KEY  = os.environ.get("VISION_API_KEY", "")
MODEL    = os.environ.get("VISION_MODEL", "glm-4v")
HERE = os.path.dirname(os.path.abspath(__file__))


def post(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_BASE.rstrip("/") + "/chat/completions", data=data, method="POST")
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


def gen_sentences(plain_text, max_retries=2):
    prompt = (
        "以下是英语阅读全文（可能含多段）。请按自然句拆分成句子数组，返回 JSON 数组，"
        "每个元素为对象：{\"en\": 原句英文（保留原拼写，不要改写）, "
        "\"zh\": 该句中文翻译, \"analysis\": 该句的语法/结构拆解（用简洁中文，点出主干、从句、重点词组，可用换行分隔要点）}。"
        "保持原句先后顺序，不要解释、不要 markdown 围栏。\n\n" + plain_text)
    for attempt in range(max_retries + 1):
        try:
            content = post({
                "model": MODEL, "temperature": 0.2, "max_tokens": 2048,
                "messages": [
                    {"role": "system", "content": "你是严谨的英语句子分析助手，擅长中学阅读长难句拆解。"},
                    {"role": "user", "content": prompt},
                ],
            })
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2); continue
            raise RuntimeError(f"句子分析 API 出错：{e}")
        res = parse_json(content)
        if isinstance(res, list) and res and all(isinstance(x, dict) and "en" in x for x in res):
            return res
        if attempt < max_retries:
            time.sleep(2); continue
    raise RuntimeError("句子分析返回非预期结构：" + str(content)[:300])


def main():
    if not API_KEY:
        sys.exit("未设置 VISION_API_KEY 环境变量")
    path = os.path.join(HERE, "_ocr_result.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for p in data["passages"]:
        plain = re.sub(r"<[^>]+>", " ", p.get("text", ""))
        plain = re.sub(r"\s+", " ", plain).strip()
        if not plain:
            continue
        print(f"→ 生成篇章 {p.get('id')} 逐句精读数据 ...", file=sys.stderr, flush=True)
        try:
            sents = gen_sentences(plain)
        except RuntimeError as e:
            print("  ✘ " + str(e), file=sys.stderr); continue
        p["sentences"] = sents
        print(f"   ✔ {len(sents)} 句", file=sys.stderr)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✔ 已写入 _ocr_result.json 的 sentences 字段", file=sys.stderr)


if __name__ == "__main__":
    main()