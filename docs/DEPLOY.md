# 部署文档

> 在线地址：https://publish.qiniu.zdwktlj.top
> 目标环境：Azure VM（Ubuntu 22.04，2 vCPU / 4GB），与另两个项目共机，本项目固定 **8082 端口** + 独立目录 `/opt/multi-publish` + 独立子域名（见复盘 D-11）。

## 架构

```
用户浏览器 ──HTTPS 443──> Caddy（自动 Let's Encrypt）
                          ├── 静态资源  /opt/multi-publish/frontend/dist
                          └── /platforms /adapt /health  ──反代──> 后端容器 :8082 ──> DeepSeek API
```

- 后端：Docker Compose 跑 FastAPI 容器（端口 8082）。
- 前端：VM 上 `npm run build` 产出静态 `dist/`，Caddy 直接托管。
- HTTPS：Caddy 自动签发并续期证书（剪贴板 API 的硬前提）。
- 多项目隔离：Caddy 用 `conf.d` drop-in，每项目一个 `.caddy` 文件，互不冲突。

## 首次部署

前提：VM 已装 Docker、Caddy；域名 A 记录已指向 VM 公网 IP；NSG 放行 80/443。

```bash
# 1. 安装 Node 20（构建前端用）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. 拉代码
sudo mkdir -p /opt/multi-publish && sudo chown "$USER" /opt/multi-publish
git clone https://github.com/tljcpa/qiniu-multi-publish.git /opt/multi-publish
cd /opt/multi-publish

# 3. 配置后端密钥（不入 git）
cat > backend/.env <<EOF
PORT=8082
DEEPSEEK_API_KEY=<你的 DeepSeek Key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
EOF
chmod 600 backend/.env

# 4. 起后端容器
sudo docker compose up -d --build backend
curl -fsS http://127.0.0.1:8082/health      # 期望 {"status":"ok"}

# 5. 构建前端
cd frontend && npm install && npm run build && cd ..

# 6. 配置 Caddy（drop-in，不动其它项目）
sudo mkdir -p /etc/caddy/conf.d
sudo cp deploy/multi-publish.caddy /etc/caddy/conf.d/multi-publish.caddy
grep -q "conf.d" /etc/caddy/Caddyfile || \
  echo 'import /etc/caddy/conf.d/*.caddy' | sudo tee -a /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
```

完成后访问 https://publish.qiniu.zdwktlj.top 即可。

## 日常更新

```bash
cd /opt/multi-publish && bash deploy/update.sh
```

`deploy/update.sh` 会：拉 main → 重建重启后端容器 → 重新构建前端 → 重载 Caddy → 健康检查。

## 常见问题

- **剪贴板按钮无效**：确认走的是 HTTPS（`navigator.clipboard` 仅安全上下文可用）。前端已做 execCommand 兜底。
- **/adapt 报错**：检查 `backend/.env` 的 `DEEPSEEK_API_KEY` 与余额；`sudo docker compose logs backend` 看日志。
- **证书没签发**：确认 80/443 放行、域名解析生效；`sudo journalctl -u caddy` 看 Caddy 日志。
- **改了前端没生效**：需重新 `npm run build`（Caddy 服的是 `dist/`，不是源码）。
