#!/bin/bash
# PHOENIX Server 启动脚本
# 用法: ./start-server.sh [--background]

PORT=8765
HOST="127.0.0.1"
PHOENIX_HOME="$HOME/.claude/phoenix"
LOG_FILE="/tmp/phoenix-server.log"

# 检查是否已在运行
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ PHOENIX 服务器已在运行 (端口 $PORT)"
    echo "  访问: http://$HOST:$PORT/viz"
    exit 0
fi

# 启动服务器
if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
    echo "启动 PHOENIX 服务器 (后台模式)..."
    cd "$PHOENIX_HOME" && nohup python3 server.py --port $PORT --host $HOST > "$LOG_FILE" 2>&1 &
    sleep 2
    if lsof -i :$PORT > /dev/null 2>&1; then
        echo "✓ 服务器启动成功"
        echo "  PID: $(lsof -ti :$PORT)"
        echo "  日志: $LOG_FILE"
        echo "  访问: http://$HOST:$PORT/viz"
    else
        echo "✗ 服务器启动失败，查看日志: $LOG_FILE"
        exit 1
    fi
else
    echo "启动 PHOENIX 服务器 (前台模式)..."
    echo "访问: http://$HOST:$PORT/viz"
    echo "按 Ctrl+C 停止"
    cd "$PHOENIX_HOME" && python3 server.py --port $PORT --host $HOST
fi
