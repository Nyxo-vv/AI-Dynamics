#!/bin/bash
# AI Dynamics 一键启动脚本
# 启动 Ollama、后端、前端三个服务，Ctrl+C 一键停止全部

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "正在停止所有服务..."
    kill $PID_OLLAMA $PID_BACKEND $PID_FRONTEND 2>/dev/null
    wait $PID_OLLAMA $PID_BACKEND $PID_FRONTEND 2>/dev/null
    echo "已停止。"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 1. Ollama
echo "▶ 启动 Ollama..."
ollama serve &
PID_OLLAMA=$!
sleep 2

# 2. 后端
echo "▶ 启动后端 (port 9100)..."
cd "$ROOT_DIR/backend"
source "$ROOT_DIR/.venv/bin/activate"
python3.12 main.py &
PID_BACKEND=$!
sleep 2

# 3. 前端
echo "▶ 启动前端 (port 5173)..."
cd "$ROOT_DIR/frontend"
npm run dev &
PID_FRONTEND=$!

echo ""
echo "✓ 全部启动完成"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:9100"
echo "  按 Ctrl+C 停止所有服务"
echo ""

wait
