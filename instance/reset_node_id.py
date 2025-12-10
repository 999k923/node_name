#!/usr/bin/env python3
# reset_id_only_safe.py
import os
import sqlite3

DB_FILE = "nodes.db"
OFFSET = 100000  # 临时偏移量，保证不冲突

# 数据库不存在时自动创建
if not os.path.exists(DB_FILE):
    print(f"⚠️ 数据库文件 {DB_FILE} 不存在，自动创建...")
    conn = sqlite3.connect(DB_FILE)
    conn.close()
    exit(0)  # 文件刚创建，没有节点，直接退出

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 检查 node 表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node';")
if not cursor.fetchone():
    print("⚠️ node 表不存在，跳过 ID 重置")
    conn.close()
    exit(0)

# 获取所有节点的当前 ID
cursor.execute("SELECT id FROM node ORDER BY sort_order, id;")
rows = cursor.fetchall()
if len(rows) == 0:
    print("数据库为空，无需重置 ID")
    conn.close()
    exit(0)

# 第一步：先加上偏移量，避免 UNIQUE 冲突
for old_id, in rows:
    cursor.execute("UPDATE node SET id = id + ? WHERE id = ?;", (OFFSET, old_id))

# 第二步：重新生成连续 ID
for new_id, (old_id,) in enumerate(rows, start=1):
    cursor.execute("UPDATE node SET id = ? WHERE id = ?;", (new_id, old_id + OFFSET))

conn.commit()
conn.close()
print("✅ 节点 ID 已重新生成连续序号，节点顺序保持不变！")
