# 部署指南 · 阅读互动课件生成器（网页版）

## 一键部署到 Vercel（推荐，免费 + 简单）

### 1. 准备工作
- 智谱 API Key：在 [bigmodel.cn](https://bigmodel.cn) 注册获取（GLM-4V 便宜，约 0.01 元/次）
- Vercel 账号：去 [vercel.com](https://vercel.com) 用 GitHub 登录

### 2. 把项目推到 GitHub
```bash
cd 教学工具
git init && git add . && git commit -m "init"
git remote add origin <你的仓库地址>
git push -u origin main
```

### 3. 在 Vercel 导入
1. 打开 [vercel.com/new](https://vercel.com/new)
2. 选择你的 GitHub 仓库 → Import
3. **不要改任何配置**（vercel.json 已写好）
4. 点 "Environment Variables"，添加：
   - `VISION_API_KEY` = `你的智谱key`
   - `VISION_API_BASE` = `https://open.bigmodel.cn/api/paas/v4`（默认）
   - `VISION_MODEL` = `glm-4v`（默认）
5. 点 Deploy

### 4. 拿到域名
部署完成后，Vercel 会给你一个 `xxx.vercel.app` 域名。
把链接发到老师群 / 做成公众号二维码 → 老师扫码即用。

---

## 部署到阿里云函数计算（中国大陆速度更快）

适合对国内速度敏感的老师场景：

```bash
# 安装 fun 工具
npm install -g @alicloud/fun

# 在项目根目录执行（需要先有阿里云账号配置 fun）
fun deploy -y
```

或参考阿里云官方教程把 webapp/ 部署为函数。

---

## 自建 VPS 部署（完全自主）

```bash
# 1. 在服务器上装 Python 3.11+
# 2. 克隆项目
git clone <你的仓库> && cd 教学工具

# 3. 建虚拟环境 + 装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r webapp/requirements.txt

# 4. 设置环境变量
export VISION_API_KEY=你的智谱key # ⚠️ 千万不要提交到 git！建议写到 .env 或本机 shell rc
export VISION_API_BASE=https://open.bigmodel.cn/api/paas/v4
export VISION_MODEL=glm-4v

# 5. 用 gunicorn 起服务（生产）
pip install gunicorn
gunicorn webapp.app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

然后用 Nginx 反向代理 + HTTPS（推荐 Caddy 自动证书）。

---

## 本地调试

```bash
pip install -r webapp/requirements.txt
export VISION_API_KEY=你的key
uvicorn webapp.app:app --reload --port 8000
# 浏览器打开 http://localhost:8000
```

---

## 环境变量速查

| 变量名 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `VISION_API_KEY` | ✅ | — | 智谱（或其他 OpenAI 兼容）API Key |
| `VISION_API_BASE` | | `https://open.bigmodel.cn/api/paas/v4` | 视觉模型 API 地址 |
| `VISION_MODEL` | | `glm-4v` | 视觉模型名 |
| `MAX_FILES` | | `8` | 一次最多上传图数 |
| `MAX_FILE_BYTES` | | `10485760` (10MB) | 单图最大字节 |
| `DAILY_IP_LIMIT` | | `30` | 单 IP 每日软上限（防刷） |
| `FREE_TIER_LIMIT` | | `3` | 客户端免费次数（前端硬门） |

---

## 转化漏斗配置（按需调整）

- **前端免费次数**：编辑 `webapp/static/index.html` 中的 `MAX_FREE = 3`
- **群二维码**：把 `webapp/static/qr.png` 放进去，前端会自动引用；或编辑 HTML 里的 `<img id="qrImg">` 替换
- **付费墙**：可在 `/api/generate` 前置一层鉴权（如校验手机号/cookie/订单 ID）

---

## 监控 / 运营

- `/health` 返回服务端状态 + 是否配置了 key
- 服务端日志会记录每次生成（接入 Vercel Analytics 或阿里云 SLS）

---

## 常见问题

**Q: Vercel 免费额度够用吗？**
A: 每月 100GB 流量 + 100 万次函数调用。1000 个老师各生成 5 次 = 5000 次，完全够。

**Q: 智谱 key 会不会被滥用刷爆？**
A: 已加 IP 限速（30次/天/IP）+ 前端 3 次门。如担心，可把 `DAILY_IP_LIMIT` 调到 5。

**Q: 怎么换成其他视觉模型（如 GPT-4o）？**
A: 修改环境变量 `VISION_API_BASE` / `VISION_MODEL` / `VISION_API_KEY` 即可，接口是 OpenAI 兼容的。

**Q: 中国老师访问 Vercel 慢怎么办？**
A: 部署到阿里云函数计算或腾讯云 CloudBase，国内延迟 < 50ms。