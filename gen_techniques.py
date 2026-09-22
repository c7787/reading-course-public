#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_techniques.py — 为 _ocr_result.json 中各篇自动生成"考试做题技巧"
读环境变量 VISION_API_KEY / VISION_API_BASE / VISION_MODEL
用法:  export VISION_API_KEY=...  &&  python gen_techniques.py
"""
import os, sys, json, re, urllib.request, urllib.error

API_BASE = os.environ.get("VISION_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
API_KEY  = os.environ.get("VISION_API_KEY", "")
MODEL    = os.environ.get("VISION_MODEL", "glm-4v")

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT_FILE = os.path.join(HERE, "_ocr_result.json")

SYSTEM = (
    "你是英语阅读应试策略助手。根据用户给出的篇章正文与题目，"
    "输出 3-6 条**针对该篇**适用的考试做题技巧/解题方法，每条一句话、实用、可操作。"
    "风格参考：'先读题干再回原文定位关键词'、'关注同义替换，原文与选项常换词不换意'、"
    "'排除含 must/never/always 等绝对词的选项'、'主旨题关注首尾段与每段首句'。"
    "严格只输出 JSON：{\"techniques\":[\"技巧1\",\"技巧2\",\"技巧3\"]},不要任何解释、不要围栏。"
)

def parse_json_loose(text):
    """3 档容错：严格 → 宽松 → 截取首尾大括号"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try: return json.loads(text)
    except Exception: pass
    try: return json.loads(text, strict=False)
    except Exception: pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try: return json.loads(m.group(0), strict=False)
        except Exception: pass
    raise RuntimeError("无法解析: " + text[:200])

def call(prompt, retries=2):
    last = None
    for k in range(retries + 1):
        payload = {
            "model": MODEL,
            "temperature": 0.5,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": 1024
        }
        req = urllib.request.Request(
            API_BASE.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )
        req.add_header("Authorization", "Bearer " + API_KEY)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                out = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError("API %s: %s" % (e.code, e.read().decode("utf-8","ignore")[:200]))
        content = out["choices"][0]["message"]["content"]
        try:
            return parse_json_loose(content)
        except Exception as e:
            last = e
            print("  · 解析失败（第 %d 次）: %s" % (k+1, str(e)[:80]))
    raise last

def main():
    if not API_KEY:
        sys.exit("✘ 未设置环境变量 VISION_API_KEY。请先:  export VISION_API_KEY=你的key")

    with open(RESULT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    passages = data.get("passages", [])
    if not passages:
        sys.exit("✘ _ocr_result.json 中无 passages 数据。")

    changed = 0
    for p in passages:
        pid = p.get("id", "?")
        if p.get("techniques"):
            print("· %s 篇已有技巧，跳过" % pid)
            continue
        text = (p.get("text") or "").strip()
        if not text:
            continue
        # 去掉 HTML 标签，截断到合理长度
        plain = re.sub(r"<[^>]+>", " ", text)
        plain = re.sub(r"\s+", " ", plain).strip()[:4000]
        qs = p.get("questions", [])
        qtext = "\n".join(q.get("q","") for q in qs)[:1500]
        prompt = "【原文】\n" + plain + "\n\n【题目】\n" + qtext

        print("· 正在为 %s 篇生成做题技巧..." % pid)
        try:
            r = call(prompt)
        except Exception as e:
            print("  ! 调用失败: %s" % e)
            continue
        techs = r.get("techniques", [])
        if not isinstance(techs, list) or not techs:
            print("  ! 返回无 techniques 字段")
            continue
        techs = [str(x).strip() for x in techs if str(x).strip()]
        p["techniques"] = techs
        print("  ✔ 生成 %d 条" % len(techs))
        changed += 1

    if changed == 0:
        print("\n（没有需要更新的篇章）")
        return

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n✔ 已更新 %s（%d 篇新增技巧）" % (RESULT_FILE, changed))

if __name__ == "__main__":
    main()