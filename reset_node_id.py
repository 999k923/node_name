#!/usr/bin/env python3
# reset_id_and_order_safe.py
import os
import sqlite3

DB_FILE = "nodes.db"

if not os.path.exists(DB_FILE):
    print(f"⚠️ 数据库文件 {DB_FILE} 不存在！")
    exit(1)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ---------------------------
# 检查 sort_order 列是否存在
# ---------------------------
cursor.execute("PRAGMA table_info(node)")
columns = [row[1] for row in cursor.fetchall()]

if "sort_order" not in columns:
    print("⚡ 数据库缺少 'sort_order' 列，正在添加...")
    cursor.execute('ALTER TABLE node ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0')
    conn.commit()
    print("✅ 添加完成")

# ---------------------------
# 备份原数据到临时表
# ---------------------------
cursor.execute("DROP TABLE IF EXISTS node_backup")
cursor.execute("CREATE TABLE node_backup AS SELECT * FROM node ORDER BY id;")

# ---------------------------
# 清空原表
# ---------------------------
cursor.execute("DELETE FROM node;")

# ---------------------------
# 重新插入数据，ID 和 sort_order 连续
# ---------------------------
cursor.execute("SELECT name, link, enabled FROM node_backup ORDER BY id;")
rows = cursor.fetchall()

for idx, row in enumerate(rows, start=1):
    # row 是 (name, link, enabled)
    cursor.execute(
        "INSERT INTO node (name, link, enabled, sort_order) VALUES (?, ?, ?, ?);",
        (*row, idx)
    )

# ---------------------------
# 删除临时表
# ---------------------------
cursor.execute("DROP TABLE node_backup;")

conn.commit()
conn.close()

print("✅ 节点 ID 和 sort_order 已重新生成连续序号！")
