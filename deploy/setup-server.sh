#!/usr/bin/env bash
# 香港/新加坡轻量服务器一键部署（Ubuntu 22.04）
# 代码已在 GitHub：https://github.com/c7787/reading-course-public
# 用法：
#   bash setup-server.sh reading.example.com     # 有域名 → 自动 HTTPS
#   bash setup-server.sh                          # 无域名 → 用服务器 IP 走 HTTP
set -euo pipefail

DOMAIN="${1:-}"                 # 可选：你的域名
APP_DIR="/opt/reading-course"
PORT=8000
SERVICE="reading-course"
REPO="https://github.com/c7787/reading-course-public"

echo "==> 系统更新 + 基础依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3-venv python3-pip git curl gnupg debian-keyring debian-archive-keyring apt-transport-https

echo "==> 安装 Caddy（反向代理 + 自动 HTTPS）"
curl -1sLf 'https://dl.cloudflareapp.com/publish/df9df686d8399c53/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudflareapp.com/publish/df9df686d8399c53/caddy/stable/debian.deb.txt' \
  | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

echo "==> 拉取代码"
rm -rf "$APP_DIR"
git clone "$REPO" "$APP_DIR"
cd "$APP_DIR"

echo "==> Python venv + 依赖"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r webapp/requirements.txt -q

echo "==> 读取智谱 API Key"
if [[ -z "${VISION_API_KEY:-}" ]]; then
  read -rsp "  请粘贴智谱 VISION_API_KEY（输入隐藏）：" VISION_API_KEY; echo
fi
[[ -z "$VISION_API_KEY" ]] && { echo "  Key 不能为空，退出"; exit 1; }

echo "==> 写 systemd 服务"
cat > /etc/systemd/system/$SERVICE.service <<EOF
[Unit]
Description=Reading Courseware WebApp
After=network.target

[Service]
WorkingDirectory=$APP_DIR
Environment=VISION_API_KEY=$VISION_API_KEY
ExecStart=$APP_DIR/.venv/bin/gunicorn webapp.app:app -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:$PORT
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable $SERVICE
systemctl restart $SERVICE

echo "==> 配置 Caddy 反向代理"
if [[ -n "$DOMAIN" ]]; then
  cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    reverse_proxy 127.0.0.1:$PORT
}
EOF
  echo "  已配 HTTPS（Caddy 自动申请 Let's Encrypt 证书）。"
  echo "  请确保 $DOMAIN 已 A 记录解析到本机公网 IP，且安全组开放 80/443。"
else
  cat > /etc/caddy/Caddyfile <<EOF
:80 {
    reverse_proxy 127.0.0.1:$PORT
}
EOF
  echo "  未给域名 → 使用 HTTP（IP 直访）。微信扫码建议配域名+HTTPS，见 README。"
fi
systemctl restart caddy

sleep 2
echo
echo "==> 完成 ✅"
[[ -n "$DOMAIN" ]] && echo "  访问: https://$DOMAIN/   (样例: https://$DOMAIN/sample)" \
                    || echo "  访问: http://<服务器公网IP>/   (样例: http://<IP>/sample)"
echo "  验证: /health 应返回 has_api_key:true"
echo "  更新代码: cd $APP_DIR && git pull && systemctl restart $SERVICE"