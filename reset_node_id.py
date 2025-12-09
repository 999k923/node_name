# reset_node_id.py
from app import app
from models import db, Node

def reset_node_ids():
    """
    将 Node 表的 ID 重置为连续整数，从 1 开始
    """
    with app.app_context():
        nodes = Node.query.order_by(Node.id).all()  # 按原 ID 排序
        print(f"当前节点数量: {len(nodes)}")

        for idx, node in enumerate(nodes, start=1):
            node.id = idx  # 重新分配 ID

        db.session.commit()
        print("✅ 节点 ID 已重新生成连续序号！")

if __name__ == "__main__":
    reset_node_ids()
