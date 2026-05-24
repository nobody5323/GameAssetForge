#!/usr/bin/env bash
# GameAsset Forge — 一键启动 (macOS/Linux)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "============================================"
echo "  GameAsset Forge — 一键启动"
echo "============================================"
echo

# 后端
echo "[1/2] 启动后端 (uvicorn :8000)..."
cd "$SCRIPT_DIR/backend"
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
echo "       PID: $BACKEND_PID"
echo

# 前端
echo "[2/2] 启动前端 (vite :4174)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "       PID: $FRONTEND_PID"
echo

sleep 3
open http://127.0.0.1:4174 2>/dev/null || xdg-open http://127.0.0.1:4174 2>/dev/null || true

echo "============================================"
echo "  前端: http://127.0.0.1:4174"
echo "  后端: http://127.0.0.1:8000"
echo "  API文档: http://127.0.0.1:8000/docs"
echo "============================================"
echo
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
