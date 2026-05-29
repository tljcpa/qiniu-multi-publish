#!/usr/bin/env bash
# 一键更新部署（在 VM 上执行）。
# 用途：拉最新代码 -> 重建并重启后端容器 -> 重新构建前端 -> 重载 Caddy。
# 幂等可重复执行。前提：已按 docs/DEPLOY.md 完成首次安装。
set -euo pipefail

APP_DIR=/opt/multi-publish
cd "$APP_DIR"

echo "==> 拉取最新 main"
git checkout main
git pull --ff-only

echo "==> 重建并重启后端容器"
sudo docker compose up -d --build backend

echo "==> 构建前端静态资源"
cd frontend
npm install --no-audit --no-fund
npm run build
cd ..

echo "==> 重载 Caddy"
sudo systemctl reload caddy

echo "==> 健康检查"
sleep 3
curl -fsS http://127.0.0.1:8082/health && echo " backend OK"
curl -fsS -o /dev/null -w "frontend HTTP %{http_code}\n" https://publish.qiniu.zdwktlj.top/

echo "==> 完成"
