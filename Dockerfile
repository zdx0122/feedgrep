# 使用精简版镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# PYTHONUNBUFFERED=1 保证日志能实时在 docker logs 中显示
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装必要的系统工具（针对 feedgrep 可能需要的编译依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（如果你有 Web UI 或 API）
EXPOSE 8000

# 运行主程序
CMD ["python", "feedgrep.py"]
