# 📚 英语阅读互动课件生成器

> **拍张题图，30 秒生成可讲解的英语阅读课件 HTML。**
> 老师零门槛：扫码 → 拖图 → 拿到可编辑的互动课件 → 课堂直接用。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org)
[![Deploy: 云函数](https://img.shields.io/badge/deploy-国内云函数-0e8a16.svg)](deploy/CLOUD_FUNCTIONS.md)

---

## 这是什么

把英语阅读题图片（试卷/教辅/电子稿）丢进系统，AI 自动解析出：

| 模块 | 说明 |
|---|---|
| 📖 **原文 + 中文翻译** | 段段对照，A/B/C/D 分篇 |
| 🔬 **逐句精读** | 点任一句弹出翻译 + 语法拆解 |
| ❓ **互动选择题** | 点击判对错（不预弹答案），错题定位原文 |
| 📝 **考点积累** | 重难点单词 / 短语 / 高频考点 |
| 💡 **做题技巧** | per-passage 应试策略（叙事/说明文/议论各不同） |
| 🎓 **教师讲解模式** | 一键展开全部答案 + 解析 |
| 🖨 **打印 / 导 PDF** | 学生版 / 教师版双模式 |
| 🌗 **夜间模式** | 深色主题、字号可调 |

---

## 🎯 给老师用的方式（3 步）

1. **扫码** → 打开网页版（无需注册 / 下载）
2. **拖图** → 上传英语阅读题图片（最多 8 张）
3. **下载 HTML** → 浏览器打开，课堂直接讲

免费用 3 次后引导加入群/付费。

---

## 🚀 5 分钟上线（Vercel 免费部署）

```bash
# 1. 推到 GitHub
git init && git add . && git commit -m "v1.0"
git remote add origin <你的GitHub仓库地址>
git push -u origin main

# 2. 在 vercel.com/new 导入仓库
#    - 不要改任何配置（vercel.json 已写好）
#    - Environment Variables 加：VISION_API_KEY=<你的智谱key>
#    - Deploy

# 3. 拿到 xxx.vercel.app 域名 → 做成公众号二维码 → 群内推送
```

详细部署文档：[`webapp/README.md`](webapp/README.md)

| 部署平台 | 国内速度 | 难度 | 适用场景 |
|---|---|---|---|
| **Vercel** | ⚠️ 国外，国内偶卡 | ⭐ | 海外/外教/私立学校 |
| **阿里云函数计算** | ✅ <50ms | ⭐⭐ | 国内公立校主力 |
| **自建 VPS** | ✅ 可控 | ⭐⭐⭐ | 完全自主 |

---

## 🧑‍💻 本地开发

### 桌面端（macOS 一键启动）

```bash
# 双击"启动生成器.command"或在终端：
./启动生成器.command
# 或
open 英语阅读生成器.app
```

启动后浏览器开 `http://127.0.0.1:8765`，填入智谱 key 即用。

### 命令行（批处理 OCR）

```bash
export VISION_API_KEY=你的key
python3 ocr_batch.py IMG_9224.jpg IMG_9225.png      # 多图识别
python3 translate_paras.py                          # 补翻译
python3 gen_sentences.py                            # 逐句精读
python3 gen_techniques.py                           # 做题技巧
python3 inject_result.py                            # 注入模板 → 阅读课件_生成.html
```

### 公开网页版

```bash
cd webapp && pip install -r requirements.txt
export VISION_API_KEY=你的key
uvicorn webapp.app:app --port 8000
# 浏览器打开 http://localhost:8000
```

---

## 📂 目录结构

```
教学工具/
├── 阅读课件.html            ← 模板（前端单页，可直接编辑）
├── 生成讲解课件.py          ← 核心：图片 → JSON → 注入模板 → HTML
├── ocr_batch.py             ← 批量 OCR 多张题图
├── translate_paras.py       ← LLM 生成段落中文翻译
├── gen_sentences.py         ← LLM 生成逐句精读
├── gen_techniques.py        ← LLM 生成做题技巧
├── inject_result.py         ← 把 _ocr_result.json 注入模板
├── server.py                ← 本机 HTTP 服务（桌面端 GUI 后端）
├── 启动生成器.command        ← macOS 一键启动
├── 英语阅读生成器.app/        ← macOS App 包（双击启动）
│
├── webapp/                  ← 公开网页版（部署用）
│   ├── app.py               ← FastAPI 后端
│   ├── api/index.py         ← Vercel 入口
│   ├── static/              ← 自包含前端
│   ├── requirements.txt
│   └── README.md            ← 详细部署文档
│
├── vercel.json              ← Vercel 部署配置
├── .env.example             ← 环境变量模板（复制成 .env 填值）
├── .gitignore
└── LICENSE                  ← MIT
```

---

## 💰 成本估算

| 项 | 单价 | 1000 老师 × 3 免费次 |
|---|---:|---:|
| 智谱 glm-4v（每张图） | ~0.01 元 | ~30 元 |
| Vercel 免费额度 | 100GB 流量 + 100 万次/月 | 0 元 |
| **合计** | | **~30 元** |

---

## 🔒 安全 / 隐私

- ✅ API key 仅服务端持有，浏览器零泄露
- ✅ 图片处理完立即丢弃，不落盘（除生成 HTML）
- ✅ 下载文件落 `/tmp/`（serverless 只读文件系统自动回退），重启即清
- ✅ IP 软上限 30 次/天防刷
- ✅ 客户端本地限 3 次免费（可绕过，但 IP 层兜底）

---

## 🤝 贡献 / 二次开发

- 改前端：编辑 [`阅读课件.html`](阅读课件.html)，单独打开就能预览
- 改识别逻辑：编辑 [`生成讲解课件.py`](生成讲解课件.py) 的 `SYSTEM_PROMPT` / `call_vision()`
- 换视觉模型：环境变量 `VISION_API_BASE` / `VISION_MODEL`，接口 OpenAI 兼容即可

---

## 📬 联系

- 作者：陈万里（揭阳）
- 项目处于早期，欢迎反馈 / 建议 / 合作

## License

MIT — 详见 [LICENSE](LICENSE)