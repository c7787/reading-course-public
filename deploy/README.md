# 香港/新加坡轻量服务器部署指南

Vercel 在大陆访问不稳定，故改用**香港/新加坡轻量应用服务器**（免备案、国内 50-80ms）。
代码已在 GitHub，服务器直接 clone，跑一条命令上线。

## 1. 买服务器（约 30-60 元/月）

| 厂商 | 推荐配置 | 备注 |
|---|---|---|
| 腾讯云国际版 | 轻量应用服务器 香港 / 新加坡，1C2G | 新用户常 24 元/月 |
| 阿里云国际版 | ECS / 轻量 香港 | 同上 |
| UCloud | 香港快杰 | 按量也便宜 |
| 雨云 / 橘子数码 | 香港 CN2 | 小众但便宜 |

系统选 **Ubuntu 22.04 LTS**（脚本按这个写）。
安全组：开放 **22（SSH）/ 80 / 443**（若有域名）。纯 IP 模式只需 80。

## 2. SSH 进服务器

```bash
ssh root@<你的服务器公网IP>
```

## 3. 一键部署

```bash
# 有域名（推荐，自动 HTTPS）
curl -fsSL https://raw.githubusercontent.com/c7787/reading-course-public/main/deploy/setup-server.sh -o setup.sh
bash setup.sh reading.example.com     # 换成你的域名

# 或：无域名，先用 IP 走 HTTP
bash setup.sh
```

脚本会自动：装 Python venv + 依赖 → clone 代码 → 写 systemd 服务 → 装 Caddy → 配反代 → 启动。
中途会让你粘贴**智谱 VISION_API_KEY**（输入隐藏，写进 systemd 环境变量，不落盘到代码）。

## 4. 验证

```bash
curl https://reading.example.com/health
# 或 IP 模式：
curl http://<IP>/health
```

应返回：`{"ok":true,"has_api_key":true,"model":"glm-4v",...}`

## 5. 日常运维

```bash
# 更新代码
cd /opt/reading-course && git pull && systemctl restart reading-course

# 看日志
journalctl -u reading-course -f

# 换 key
systemctl edit reading-course   # 改 Environment=VISION_API_KEY=...
systemctl restart reading-course

# 看 Caddy 状态
systemctl status caddy
```

## 6. 域名 + HTTPS（强烈建议）

微信扫码打开网页时，**HTTP 链接会弹"不安全"警告**，转化掉。所以：

1. 买个域名（阿里云/腾讯云/Namesilo，约 30-70 元/年）
2. 给域名加 **A 记录** → 指向服务器公网 IP
3. 重跑：`bash setup.sh 你的域名`
4. Caddy 自动申请 Let's Encrypt 证书（需 80 端口可访问）

完成后老师扫码 → https 链接 → 无警告 → 体验顺畅。

## 7. 成本

| 项 | 月费 |
|---|---|
| 香港轻量服务器 1C2G | ~30-60 元 |
| 域名 | ~3-6 元/月 |
| 智谱 glm-4v（按量） | 1000 老师 × 3 次 ≈ 30 元 |
| **合计** | **~70-100 元/月** |

## 常见坑

- **Caddy 申请证书失败**：检查 80 端口是否开放、域名 A 记录是否生效（`dig 你的域名` 看是否指向服务器 IP）。
- **gunicorn 起不来**：看 `journalctl -u reading-course`，多半是 venv 路径或依赖没装全。
- **大陆访问仍慢**：香港节点偶尔抽风 → 换新加坡节点，或升级到 CN2 GIA 线路（贵些但稳）。
- **管理面板**：若想要图形界面，可装 1Panel /宝塔（但命令行已够用）。
