from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SubscriptionGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1024), nullable=False)  # 原始订阅链接

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # 备注
    link = db.Column(db.String(1024), nullable=False) # 完整节点链接
    enabled = db.Column(db.Boolean, default=True)

    group_id = db.Column(db.Integer, db.ForeignKey('subscription_group.id'), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
