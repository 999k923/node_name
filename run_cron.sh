#!/bin/bash

while true; do
    echo "[Cron] 执行 reset_id_only_safe.py ..."
    python3 /app/instance/reset_node_id.py
    echo "[Cron] 完成，等待 1 小时..."
    sleep 3600
done
