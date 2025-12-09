# 基于官方 Python 3.12 slim 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir requests gunicorn

# 复制项目文件
COPY . .

# 初始化数据库（如果不存在）
RUN python db_init.py || true

# 暴露 Flask 端口
EXPOSE 5786

# 启动命令
CMD ["gunicorn", "-b", "0.0.0.0:5786", "app:app"]
