# 后端镜像（PR1 占位骨架，完整部署配置在 PR14 完善）。
FROM python:3.11-slim

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝应用代码
COPY app ./app
COPY adapters ./adapters

# 本项目固定 8082 端口（同机三项目隔离）
EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
