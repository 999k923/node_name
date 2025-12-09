#!/bin/bash
# stop_node.sh - 一键停止 Node Subscription Manager 并退出虚拟环境

APP_DIR="/root/node_name"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="node_sub"

echo "=== 停止 systemd 服务 ==="
sudo systemctl stop $SERVICE_NAME
echo "服务已停止。"

echo "=== 取消开机自启 ==="
sudo systemctl disable $SERVICE_NAME
echo "开机自启已取消。"

echo "=== 检查服务状态 ==="
sudo systemctl status $SERVICE_NAME --no-pager -n 20

# ---------------------------
# 退出虚拟环境（如果当前 shell 已激活）
# ---------------------------
if [[ "$VIRTUAL_ENV" == "$VENV_DIR" ]]; then
    deactivate
    echo "已退出虚拟环境。"
else
    echo "当前 shell 未激活虚拟环境，无需退出。"
fi

echo "✅ 操作完成。"
