#!/bin/bash

# OpenChoreo 實戰 Codelabs 本機預覽伺服器

REQUESTED_PORT=${1:-8088}

# 使用 Python 测试实际可 bind 的端口（100% 精准检测并自动避开已被占用的端口）
ACTUAL_PORT=$(python3 -c "
import socket

requested = int('$REQUESTED_PORT') if '$REQUESTED_PORT'.isdigit() else 8088
candidates = [requested, 8088, 9000, 8888, 9999, 8081, 8082, 8000]
seen = set()
order = []
for c in candidates:
    if c not in seen:
        seen.add(c)
        order.append(c)

selected = None
for p in order:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', p))
        s.close()
        selected = p
        break
    except OSError:
        continue

print(selected if selected is not None else requested)
" 2>/dev/null || echo "${REQUESTED_PORT}")

if [ "$ACTUAL_PORT" != "$REQUESTED_PORT" ]; then
    echo "⚠️  端口 $REQUESTED_PORT 已被其他服务（如 k3d 容器）占用。"
    echo "🔄 自动切换至可用端口: $ACTUAL_PORT"
fi

PORT=$ACTUAL_PORT

echo "================================================"
echo "🔭 OpenChoreo 實戰 Codelabs 本地伺服器"
echo "================================================"
echo ""
echo "🚀 HTTP 伺服器啟動於端口: $PORT"
echo ""
echo "🌐 存取教學："
echo "  📌 課程首頁: http://localhost:$PORT"
echo ""
echo "按 Ctrl+C 停止伺服器"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/generated"

# 启动 HTTP 伺服器
python3 -m http.server "$PORT"
