# 国内云函数部署指南（腾讯云 CloudBase / 阿里云 FC）

比香港轻量服务器更省：云函数**按量付费，量小基本 0 元/月**，国内访问 <50ms，免备案。
代码已在 GitHub，云函数直接从仓库拉或上传代码包即可。

> 适用前提：`webapp/app.py` 已适配 serverless（下载目录自动退到 `/tmp/`，端口由平台注入）。
> 部署包 = **整个项目根目录**（含 `webapp/` + 根目录 `生成讲解课件.py`，后者被 `webapp/app.py` 通过 `sys.path` 引用）。

## 核心启动命令（两个平台通用）

云函数用「Web 函数 / 自定义运行时」模式，启动命令都是：

```bash
gunicorn webapp.app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-9000}
```

- 端口：腾讯云 CloudBase 约定 `9000`；阿里云 FC 注入环境变量 `$PORT`（用 `${PORT:-9000}` 兜底）
- 依赖：根目录 `requirements.txt`（fastapi / uvicorn / python-multipart / **gunicorn**）由云函数自动安装；`webapp/requirements.txt` 内容相同，供本地开发用
- 环境变量：在控制台配置 `VISION_API_KEY=你的智谱key`（**不要写进代码**）

---

## 方案 A：腾讯云 CloudBase（推荐，控制台最友好）

1. 打开 [cloud.tencent.com/product/tcb](https://cloud.tencent.com/product/tcb) → 开通「云开发 CloudBase」
2. 新建环境（选「按量计费」，有免费额度）
3. 左侧 **云函数** → **新建云函数**
   - 函数类型：**Web 函数**
   - 运行环境：Python 3.10
   - 上传方式：选「本地上传文件夹」→ 选**项目根目录**（含 webapp/ 和 生成讲解课件.py）
   - 或「代码托管」→ 关联 GitHub 仓库 `c7787/reading-course-public`
4. 函数配置：
   - 入口命令（启动命令）：填上面的 gunicorn 命令
   - 环境变量：`VISION_API_KEY` = 你的智谱 key
5. 在函数「触发管理」里开启 **HTTP 访问服务** → 拿到一个 `*.apigw.tencentcs.com` 域名
6. 访问 `https://<你的域名>/health` 验证 `has_api_key:true`
7. （可选）绑定自定义域名 + 免费 HTTPS（CloudBase 控制台「域名管理」）

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
