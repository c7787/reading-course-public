#!/bin/bash
# 英语阅读生成器 启动脚本：双击 .app 即运行，无需终端操作
PROJ="$(cd "$(dirname "$0")/../../.." && pwd)"
PY="/Users/mini/.workbuddy-ai/binaries/python/versions/3.13.12/bin/python3"
[ -x "$PY" ] || PY="python3"
cd "$PROJ" || exit 1

# 关键：让本机回环地址 127.0.0.1/localhost 绕过任何系统或软件代理，
# 否则装有代理/VPN/校园网客户端时，浏览器和 curl 会被代理拦截导致“打不开”。
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

# 若端口已被占用（上一次的服务还在跑），直接打开即可，无需重复启动
if curl -s --noproxy 127.0.0.1 -o /dev/null http://127.0.0.1:8765/ 2>/dev/null; then
  open http://127.0.0.1:8765/
  exit 0
fi

# 后台启动本地服务（日志写到 /tmp，便于排查）
nohup "$PY" "$PROJ/server.py" > "/tmp/英语阅读生成器.log" 2>&1 &

# 等服务真正就绪（直连本机，绕过代理），最多等 15 秒
for i in $(seq 1 30); do
  if curl -s --noproxy 127.0.0.1 -o /dev/null http://127.0.0.1:8765/ 2>/dev/null; then break; fi
  sleep 0.5
done
open http://127.0.0.1:8765/
