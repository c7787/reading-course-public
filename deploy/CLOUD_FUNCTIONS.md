# 国内云函数部署指南（腾讯云 CloudBase / 阿里云 FC）

比香港轻量服务器更省：云函数**按量付费，量小基本 0 元/月**，国内访问 <50ms，免备案。
代码已在 GitHub，云函数直接从仓库拉或上传代码包即可。

> 适用前提：`webapp/app.py` 已适配 serverless（下载目录自动退到 `/tmp/`，端口由平台注入）。
> 部署包 = **整个项目根目录**（含 `webapp/` + 根目录 `生成讲解课件.py`，后者被 `webapp/app.py` 通过 `sys.path` 引用）。

## 平台速辨（腾讯云有两套容易混的产品）
- **云开发 CloudBase**（方案 A）：左侧菜单是「环境 / 云函数 / 云数据库 …」，环境隔离。**有「Web 函数」类型**（和事件函数并列）。
- **云函数 SCF（独立）**（方案 C）：左侧菜单是「云函数 / 云托管」，函数本身只是事件函数，**没有 Web 函数**，要 HTTP 必须配 API 网关触发。
- 阿里云函数计算 FC（方案 B）：见下文。

## 核心启动命令（两个平台通用）

云函数用「Web 函数 / 自定义运行时」模式（方案 A、B），启动命令都是：

```bash
gunicorn webapp.app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-9000}
```

- 端口：腾讯云 CloudBase 约定 `9000`；阿里云 FC 注入环境变量 `$PORT`（用 `${PORT:-9000}` 兜底）
- 依赖：根目录 `requirements.txt`（fastapi / uvicorn / python-multipart / **gunicorn**）由云函数自动安装；`webapp/requirements.txt` 内容相同，供本地开发用
- 环境变量：在控制台配置 `VISION_API_KEY=你的智谱key`（**不要写进代码**）

> **方案 C（腾讯云独立云函数 SCF）不需要这条 gunicorn 命令**——它走的是 API 网关 + 同步 handler，入口是 `webapp.scf_main.main_handler`（已写好，零配置）。

---

## 方案 A：腾讯云 CloudBase（推荐，控制台最友好）

1. 打开 [cloud.tencent.com/product/tcb](https://cloud.tencent.com/product/tcb) → 开通「云开发 CloudBase」
2. 新建环境（选「按量计费」，有免费额度）
3. 左侧 **云函数** → **新建云函数**，在弹出的表单里：
   - **函数类型（关键！）**：这一栏默认是「事件函数」，**右边紧挨着一个「Web 函数」单选/卡片，点它**。找不到就左右看一眼，它不是单独的菜单项，而是和「事件函数」并列的那一行里的第二个选项。
   - 运行环境：Python 3.10
   - 上传方式：选「本地上传文件夹」→ 选**项目根目录**（含 webapp/ 和 生成讲解课件.py）；或「代码托管」→ 关联 GitHub 仓库 `c7787/reading-course-public`
4. 函数配置：
   - 入口命令（启动命令）：填上面的 gunicorn 命令
   - 环境变量：`VISION_API_KEY` = 你的智谱 key
5. 在函数「触发管理」里开启 **HTTP 访问服务** → 拿到一个 `*.apigw.tencentcs.com` 域名
6. 访问 `https://<你的域名>/health` 验证 `has_api_key:true`
7. （可选）绑定自定义域名 + 免费 HTTPS（CloudBase 控制台「域名管理」）

> **备用方案（少数旧版/包年包月环境看不到「Web 函数」选项时）**：
> 选「事件函数」正常建函数并上传代码 → 在「触发管理」里**新建 API 网关触发 / HTTP 触发**拿到公网地址。
> 此模式下 gunicorn 常驻服务跑不起来，需要把 `webapp/app.py` 改成 CloudBase 的 `main_handler(event, context)` 入口（不再是 gunicorn）。需要的话告诉我「走备用方案」，我把代码改好。

---

## 方案 B：阿里云函数计算 FC（按量，国内快）

1. 打开 [fc.console.aliyun.com](https://fc.console.aliyun.com) → 开通函数计算
2. 新建函数 → 选「**使用自定义运行时平滑迁移 Web Server**」或「Web 函数」
   - 运行环境：Python 3.10
   - 上传代码：本地 zip（项目根目录）/ 或从「代码仓库」拉 GitHub
3. 启动命令：`gunicorn webapp.app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-9000}`
4. 环境变量：`VISION_API_KEY` = 你的智谱 key
5. 触发器：创建 **HTTP 触发器** → 拿到 `*.fc.aliyuncs.com` 域名
6. 访问 `/health` 验证
7. （可选）自定义域名 + HTTPS（FC 控制台「域名管理」）

> 阿里云 FC 免费额度：每月 100 万次调用 + 40 万 GB-秒，小流量项目≈免费。

---

## 方案 C：腾讯云云函数 SCF（独立云函数，控制台是「云函数 / 云托管」）

> **适用场景**：你打开的是 `console.cloud.tencent.com/scf` 这种左侧菜单「云函数 / 云托管」分开的页面。SCF 没有「Web 函数」概念，所有函数都是事件函数，HTTP 访问靠 **API 网关触发器**。
> 我们已经写好 SCF 入口 `webapp/scf_main.py`，不用 gunicorn，直接同步跑 FastAPI ASGI。

### C.1 在项目根目录打 zip
```bash
cd 教学工具/
zip -r reading-course-scf.zip . \
  -x "*.git*" "*__pycache__*" "*.workbuddy-ai*" "*/.env" \
       "*_ocr_result.json" "*阅读课件_生成.html" "*.DS_Store"
```
zip 根目录必须能看到 `webapp/` 和 `生成讲解课件.py`。

### C.2 控制台新建云函数
1. 进入 [云函数 SCF 控制台](https://console.cloud.tencent.com/scf) → **函数服务** → **新建**
2. 选择 **「从头开始」** → 运行环境：**Python 3.10**
4. **提交方法**：选「**本地上传 ZIP**」→ 选刚才的 `reading-course-scf.zip」
5. **执行方法（Handler）**：填 `webapp.scf_main.main_handler`（点格式：模块路径.函数名）
6. 内存：建议 256MB 或以上；超时：建议 30 秒（OCR + 翻译要排队）
7. **环境变量**：加 `VISION_API_KEY = 你的智谱key`
8. 点「完成」创建函数

### C.3 配 API 网关触发器（关键步骤，给函数一个公网地址）
1. 进函数详情 → **触发管理** → **创建触发**
2. 触发方式选 **「API 网关触发」**
3. 选「**新建 API**」（或关联已有的）：
   - 服务名：默认
   - 前端路径：`/`（或 `/reading`）
   - 方法：**ANY**（或分别建 GET / POST）
   - 后端服务：默认走 SCF，后端路径留空
4. 启用「集成响应」：**关闭**（关掉才能正确透传 Content-Type 和 multipart）
5. 点击「发布服务」→ 在服务列表点「发布」到「release」环境
6. 拿到公网地址，形如：`https://service-xxxxxx.apigw.tencentcs.com/release/`

### C.4 验证
```bash
curl https://service-xxxxxx.apigw.tencentcs.com/release/health
# 期望：{"ok":true,"has_api_key":true,"model":"glm-4v",...}
```
浏览器打开 `.../release/` 看落地页，`/release/sample` 看样例。

### C.5 常见坑
- **找不到 handler**：执行方法必须是 `webapp.scf_main.main_handler`（别漏了 webapp 前缀，zip 根目录是项目根，不是 webapp/）。
- **集成响应开着**：会强制把所有响应包成 JSON。**一定要关掉**，否则 HTML 课件页面会被包成 base64 文本，前端拿不到可用的 HTML。
- **multipart 不通**：API 网关默认 4MB 请求体限制；上传大图会 413。在 API 网关控制台 → 服务 → 「使用API网关」改请求体上限（最大 ~10MB）。
- **路径带 `/release/`**：API 网关默认发布到 release 环境。如果你想去掉这个前缀，在 API 网关「自定义域名」里绑域名即可。
- **冷启动慢**：首次约 1-3s，正常。

---

## 验证

```bash
curl https://<你的云函数域名>/health
# 应返回 {"ok":true,"has_api_key":true,"model":"glm-4v",...}
```

访问 `https://<域名>/` 即落地页，`/sample` 看效果。

## 成本对比

| 方案 | 月费 | 国内延迟 | 备注 |
|---|---|---|---|
| 香港轻量服务器 | 30-60 元 | 50-80ms | 常驻、完全自主 |
| **腾讯云/阿里云函数** | **≈0 元（量小）** | **<50ms** | 按量、免备案、最省 |
| Vercel | 0 元 | 大陆打不开 | 已排除 |

## 运维

- **更新代码**：重新上传 / 重新关联 GitHub 拉取
- **换 key**：控制台改环境变量 `VISION_API_KEY` 后重启函数
- **看日志**：平台控制台「日志」标签
- **域名 HTTPS**：建议绑定自己的域名（国内注册约 30-70 元/年），老师扫码无"不安全"警告

## 常见坑

- **403/404**：确认「Web 函数」模式 + 启动命令绑定的是 `${PORT}`（阿里云）或 `9000`（腾讯云）
- **import 失败**：确认上传的是**项目根目录**（`webapp/app.py` 需要同级的 `生成讲解课件.py`），不是只传 webapp/
- **key 未生效**：`/health` 显示 `has_api_key:false` → 环境变量名拼错或没重启函数
- **冷启动慢**：函数闲置后首次请求会冷启动（1-3s），正常现象；可开「预留实例」消除（但要花钱）
