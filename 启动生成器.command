#!/bin/bash
# 备用启动方式：双击本文件（.command）亦可启动生成器（会打开终端窗口，便于看报错）
PROJ="$(cd "$(dirname "$0")" && pwd)"
PY="/Users/mini/.workbuddy-ai/binaries/python/versions/3.13.12/bin/python3"
[ -x "$PY" ] || PY="python3"
cd "$PROJ" || exit 1

# 让本机回环地址绕过代理，避免装有代理/VPN 时打不开
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

echo "正在启动英语阅读生成器…（本窗口可保持打开，关闭它不影响已在运行的网页）"
"$PY" "$PROJ/server.py"
open http://127.0.0.1:8765/
