#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_sample.py — 生成 webapp/static/sample.html（首屏"看效果"链接用）
跑法:  python webapp/make_sample.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from 生成讲解课件 import render_filled_template  # noqa: E402

# 中文内嵌引号统一用 「」（CJK 直角引号，不与 Python 字符串界定符冲突）

A_TEXT = (
    "<h3>The Old Man's Garden</h3>"
    "<p>An old man lived in a small village. Every morning he <b>woke up</b> early and "
    "<b>took care of</b> his garden.</p>"
    "<p>One day, a young boy asked him, 「Why do you work so hard? You are already very old.」</p>"
    "<p>The old man smiled and said, 「My dear boy, if I stop working today, "
    "the garden will forget me tomorrow.」</p>"
)

A_TRANS = (
    "<p>一个小村子里住着一位老人。每天早晨他很早起床，照料他的花园。</p>"
    "<p>一天，一个小男孩问他：「你为什么这么努力工作？你已经很老了。」</p>"
    "<p>老人笑着说：「亲爱的孩子，如果我今天停止劳作，明天花园就会忘记我。」</p>"
)

B_TEXT = (
    "<h3>Why Walking Helps You Think</h3>"
    "<p>Walking is one of the <b>simplest</b> forms of exercise, but scientists have found "
    "that it does more than keep your body healthy.</p>"
    "<p>Studies show that a short walk can boost your creativity by up to 60 percent. "
    "When you walk, your brain enters a relaxed state that <b>allows</b> new ideas to appear.</p>"
    "<p>So next time when you feel stuck on a problem, try walking away from your desk for ten minutes.</p>"
)

B_TRANS = (
    "<p>步行是最简单的运动形式之一，但科学家发现它不仅能保持身体健康。</p>"
    "<p>研究表明，短时间的散步可以让创造力提升多达 60%。当你走路时，你的大脑进入一种放松状态，"
    "从而让新想法得以涌现。</p>"
    "<p>所以下次当你被一个问题困住时，试着离开书桌走十分钟。</p>"
)

BLANK = {
    "text": "<h3>__PID__ 篇 ·（占位）</h3><p>（在此粘贴 __PID__ 篇阅读原文）</p>",
    "trans": "<p>（对应中文翻译）</p>",
    "sentences": [],
    "questions": [{
        "q": "1. （在此填写题干）",
        "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
        "answer": "B", "explain": "（在此填写解析）", "locate": "",
    }],
    "words": ["（重难点单词，每行一条）"],
    "phrases": ["（重点短语，每行一条）"],
    "points": ["（高频考点，每行一条）"],
    "techniques": ["（在此填写做题技巧）"],
}

SAMPLE = {"passages": [
    {
        "id": "A",
        "text": A_TEXT, "trans": A_TRANS,
        "sentences": [
            {"en":"An old man lived in a small village.",
             "zh":"一位老人住在一个小村子里。",
             "analysis":"主系表结构：主语 An old man + 谓语 lived（实义动词「住」）+ 地点状语 in a small village。"},
            {"en":"Every morning he woke up early and took care of his garden.",
             "zh":"每天早晨他很早醒来，照料他的花园。",
             "analysis":"时间状语 Every morning + 主语 he + 两个并列谓语 woke up early 与 took care of his garden（and 连接并列谓语）。"},
            {"en":"「Why do you work so hard? You are already very old.」",
             "zh":"「你为什么这么努力工作？你已经很老了。」",
             "analysis":"直接引语内含两句：① why 引导的宾语从句（作 asked 的宾语）；② 主系表 you are very old，already 为副词作状语。"},
            {"en":"The old man smiled and said, 「My dear boy, if I stop working today, the garden will forget me tomorrow.」",
             "zh":"老人笑着说：「亲爱的孩子，如果我今天停止劳作，明天花园就会忘记我。」",
             "analysis":"主句并列谓语 smiled and said；宾语从句内含 if 条件状语从句：if I stop working today（条件）→ 主句 the garden will forget me tomorrow（结果，will 表将来）。"},
        ],
        "questions": [
            {"q":"1. What did the old man do every morning?",
             "options":["A. Read books","B. Took care of his garden","C. Went shopping","D. Visited friends"],
             "answer":"B", "explain":"原文「Every morning he ... took care of his garden」，关键词 took care of = 照料。", "locate":"took care of his garden"},
            {"q":"2. Why did the old man work so hard according to the story?",
             "options":["A. To earn money","B. To keep the garden remembering him","C. To show off","D. Because he was bored"],
             "answer":"B", "explain":"原话「if I stop working today, the garden will forget me tomorrow」，花园忘了他是他最在意的。", "locate":"the garden will forget me tomorrow"},
            {"q":"3. The word 「take care of」 in the passage means?",
             "options":["A. 放弃","B. 修理","C. 照料/照顾","D. 喜欢"],
             "answer":"C", "explain":"take care of 是固定短语，意为「照料、照顾」，结合 garden 应理解为「照料花园」。", "locate":"took care of"},
            {"q":"4. Which of the following best describes the old man?",
             "options":["A. Lazy","B. Hard-working and wise","C. Rich","D. Strict"],
             "answer":"B", "explain":"每天早起 + 寓意深刻的话（勤劳的智慧）→ hard-working and wise。", "locate":"Every morning he woke up early"},
            {"q":"5. What can we learn from the story?",
             "options":["A. Stop working when old","B. Money is most important","C. Keep doing meaningful things","D. Ignore the garden"],
             "answer":"C", "explain":"主旨题：故事借老人之口说明坚持做有意义的事、不要停下脚步。", "locate":"if I stop working today"},
        ],
        "words": ["village — 村庄", "wake up — 醒来", "take care of — 照料", "garden — 花园", "already — 已经"],
        "phrases": ["every morning — 每天早晨", "stop doing sth — 停止做某事", "ask sb — 问某人", "smile and say — 笑着说"],
        "points": ["细节题定位原文关键词", "词义猜测题（take care of）", "人物性格推断题", "主旨大意题（首尾段+寓意）"],
        "techniques": [
            "细节题先扫题干关键词（every morning、took care of），直接回原文定位",
            "词义猜测题看上下文：「take care of + garden」大概率是「照料」，而非「修理」",
            "主旨题关注老人说的话（故事结尾的引语），通常是全文核心",
            "推断题结合人物行为+言语：每天早起 + 寓意深的话 → 勤劳且有智慧",
            "排除含 always / never 等绝对词的选项，态度题优选温和表述（B 而非 D）",
        ],
    },
    {
        "id": "B",
        "text": B_TEXT, "trans": B_TRANS,
        "sentences": [
            {"en":"Walking is one of the simplest forms of exercise, but scientists have found that it does more than keep your body healthy.",
             "zh":"步行是最简单的运动形式之一，但科学家发现它不仅能保持身体健康。",
             "analysis":"主系表 Walking is one of the simplest forms of exercise。but 转折并列句：scientists have found + that 宾语从句 it does more than keep your body healthy（more than = 不仅仅是）。"},
            {"en":"Studies show that a short walk can boost your creativity by up to 60 percent.",
             "zh":"研究表明，短时间的散步可以让创造力提升多达 60%。",
             "analysis":"主谓宾 Studies show + that 宾语从句；从句内：a short walk can boost your creativity（can 表能力）+ 程度状语 by up to 60 percent。"},
            {"en":"When you walk, your brain enters a relaxed state that allows new ideas to appear.",
             "zh":"当你走路时，你的大脑进入一种放松状态，从而让新想法得以涌现。",
             "analysis":"when 引导时间状语从句 + 主句；that 引导定语从句修饰 state：that allows new ideas to appear（allow sb/sth to do 结构）。"},
            {"en":"So next time when you feel stuck on a problem, try walking away from your desk for ten minutes.",
             "zh":"所以下次当你被一个问题困住时，试着离开书桌走十分钟。",
             "analysis":"时间状语 next time + when 引导时间状语从句 + 祈使句 try doing（try walking away...）。"},
        ],
        "questions": [
            {"q":"6. According to the passage, walking is _____. ",
             "options":["A. The most difficult exercise","B. The simplest form of exercise","C. Only good for body","D. Boring"],
             "answer":"B", "explain":"原文「Walking is one of the simplest forms of exercise」，直接定位 simplest。", "locate":"simplest forms of exercise"},
            {"q":"7. How much can walking boost creativity according to studies?",
             "options":["A. 10%","B. 30%","C. Up to 60%","D. 100%"],
             "answer":"C", "explain":"原句「boost your creativity by up to 60 percent」，关键数字 60。", "locate":"by up to 60 percent"},
            {"q":"8. What happens to your brain when you walk?",
             "options":["A. It gets tired","B. It enters a relaxed state","C. It stops working","D. It forgets things"],
             "answer":"B", "explain":"原句「your brain enters a relaxed state」，定位 relaxed state。", "locate":"relaxed state"},
            {"q":"9. The author's purpose of writing this passage is to _____. ",
             "options":["A. Sell walking shoes","B. Encourage people to walk when stuck","C. Compare walking and running","D. Criticize sitting"],
             "answer":"B", "explain":"主旨意图题：结尾句「try walking away ... for ten minutes」是建议 → 鼓励读者在被困时去散步。", "locate":"try walking away from your desk"},
            {"q":"10. The phrase 「feel stuck on」 in the last paragraph means?",
             "options":["A. 受伤","B. 兴奋","C. 卡住/困住","D. 完成"],
             "answer":"C", "explain":"结合语境「stuck on a problem」意为「被一个问题卡住」，即陷入困境。", "locate":"stuck on a problem"},
        ],
        "words": ["simplest — 最简单的", "scientist — 科学家", "creativity — 创造力", "percent — 百分比", "relaxed — 放松的"],
        "phrases": ["more than — 不仅仅是", "by up to — 多达", "feel stuck — 卡住", "walk away — 走开", "next time — 下次"],
        "points": ["细节定位题（关键词）", "数字细节题（60%）", "词义猜测题（stuck on）", "主旨意图题（作者目的）", "事实细节题"],
        "techniques": [
            "细节题定位题干关键词（simplest, 60 percent），直接回原文找同源词",
            "数字题看清单位 / 范围（by up to 60%，注意 up to 是上限）",
            "词义猜测题结合语境：stuck on a problem = 卡在一个问题上",
            "主旨意图题看结尾句的建议 / 号召（try walking away = 鼓励散步）",
            "排除法：含 most difficult / boring 等与原文 simplest 相反的选项",
        ],
    },
]}

# 组装 passages（A/B 来自样例，C/D 用模板留白）
passages = {}
for p in SAMPLE["passages"]:
    pid = p["id"]
    passages[pid] = {k: v for k, v in p.items() if k != "id"}
for k in "CD":
    if k not in passages:
        passages[k] = dict(BLANK)
        passages[k]["text"] = passages[k]["text"].replace("__PID__", k)

html = render_filled_template(passages)
out = Path(__file__).resolve().parent / "static" / "sample.html"
out.write_text(html, encoding="utf-8")
print(f"✔ 已生成: {out}")
print("  打开后可见：A、B 两篇完整样例（10 题 + 逐句精读 + 翻译 + 考点 + 做题技巧） + C/D 占位")
print("  部署到 Vercel 后访问 /sample 即可查看。")