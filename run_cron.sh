#!/bin/bash
# run_cron.sh - 每小时执行一次 reset_node_id.py

while true; do
    # 执行 ID 重置脚本
    echo "⚙️ 执行 reset_node_id.py..." >> /app/cron.log
    python3 /app/instance/reset_node_id.py >> /app/cron.log 2>&1

    # 等待一小时
    sleep 3600
done
