#!/usr/bin/env bash
# 一键部署到 Vercel
# 前置：已 npm install -g vercel 且 vercel login 完成
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> 检查 vercel CLI"
if ! command -v vercel >/dev/null 2>&1; then
  echo "    未安装。运行: npm install -g vercel"
  exit 1
fi

echo "==> 检查 git 仓库"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "    初始化 git..."
  git init
  git add .
  git commit -m "v1.0: 英语阅读互动课件生成器"
fi

echo "==> 部署到 Vercel（首次会问项目名/团队，直接回车默认即可）"
echo "    环境变量 VISION_API_KEY 请在 vercel.com dashboard 配（不写到命令行）"

# --prod 走生产环境；不带会进 preview
vercel --prod "$@"

echo
echo "==> 部署完成！"
echo "    拿到 *.vercel.app 域名后，访问 https://你的域名/health 验证"
echo "    若 has_api_key=false，说明 VISION_API_KEY 未配置，去 dashboard 配"