from flask import Flask, Response, render_template, request, redirect, url_for, flash, abort
from models import db, Node
from sqlalchemy import func
import base64
import os
import re
import string
import random
import requests
from functools import wraps
from update_node_name import update_nodes  # 更新节点名称
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nodes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret_key_for_flash"
db.init_app(app)

with app.app_context():
    if not os.path.exists("nodes.db"):
        db.create_all()

# ---------------------------
# Token
# ---------------------------
TOKEN_FILE = "access_token.txt"

def generate_token(length=20):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    else:
        token = generate_token()
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return token

# ---------------------------
# Basic Auth
# ---------------------------
WEB_USER = "mimayoudianfuza"
WEB_PASS = "zhendehenfuza"

def check_auth(username, password):
    return username == WEB_USER and password == WEB_PASS

def authenticate():
    return Response(
        '认证失败，请输入正确用户名和密码', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# 辅助函数
# ---------------------------
def reset_sort_order(group_id=None):
    """删除节点或导入订阅后，重新顺序 sort_order 从 1 开始"""
    with app.app_context():
        nodes = Node.query.filter_by(group_id=group_id).order_by(Node.sort_order).all()
        for idx, node in enumerate(nodes, start=1):
            node.sort_order = idx
        db.session.commit()

# ---------------------------
# Web 后台
# ---------------------------
@app.route("/")
@requires_auth
def index():
    nodes = Node.query.order_by(Node.group_id, Node.sort_order).all()
    # 获取所有 group_id 列表
    groups = db.session.query(Node.group_id).filter(Node.group_id != None).distinct()
    groups = [{'id': g[0], 'url': g[0]} for g in groups]  # group_id 可直接当作 URL
    token = get_token()
    return render_template("index.html", nodes=nodes, groups=groups, token=token)

# ---------------------------
# 添加单节点
# ---------------------------
@app.route("/add", methods=["POST"])
@requires_auth
def add_node():
    name = request.form.get("name", "").strip()
    link = request.form.get("link", "").strip()
    link = re.sub(r"#.*$", "", link)
    if name and link:
        # sort_order 最大 +1
        max_order = db.session.query(func.max(Node.sort_order)).scalar() or 0
        node = Node(name=name, link=link, sort_order=max_order+1)
        db.session.add(node)
        db.session.commit()
        try:
            update_nodes()
        except:
            pass
    else:
        flash("节点名称或链接不能为空", "warning")
    return redirect(url_for("index"))

# ---------------------------
# 导入订阅集合
# ---------------------------
@app.route("/import_sub", methods=["POST"])
@requires_auth
def import_sub():
    sub_url = request.form.get("sub_url", "").strip()
    if not sub_url:
        flash("订阅 URL 不能为空", "warning")
        return redirect(url_for("index"))
    try:
        r = requests.get(sub_url, timeout=10)
        content = base64.b64decode(r.text).decode()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        # group_id 用 URL 标识
        max_order = db.session.query(func.max(Node.sort_order)).scalar() or 0
        for idx, link in enumerate(lines, start=1):
            node = Node(
                name=f"节点{idx}",
                link=link,
                group_id=sub_url,
                sort_order=max_order+idx
            )
            db.session.add(node)
        db.session.commit()
        flash(f"成功导入 {len(lines)} 个节点", "success")
        reset_sort_order(sub_url)
        try:
            update_nodes()
        except:
            pass
    except Exception as e:
        flash(f"导入失败: {e}", "danger")
    return redirect(url_for("index"))

# ---------------------------
# 删除节点
# ---------------------------
@app.route("/delete/<int:node_id>")
@requires_auth
def delete_node(node_id):
    node = Node.query.get(node_id)
    if node:
        group_id = node.group_id
        db.session.delete(node)
        db.session.commit()
        reset_sort_order(group_id)
        try:
            update_nodes()
        except:
            pass
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# ---------------------------
# 删除订阅集合
# ---------------------------
@app.route("/delete_group/<path:group_id>")
@requires_auth
def delete_group(group_id):
    nodes = Node.query.filter_by(group_id=group_id).all()
    for node in nodes:
        db.session.delete(node)
    db.session.commit()
    flash(f"删除订阅集合及其 {len(nodes)} 个节点", "success")
    return redirect(url_for("index"))

# ---------------------------
# 向上移动节点
# ---------------------------
@app.route("/move_up/<int:node_id>")
@requires_auth
def move_up(node_id):
    node = Node.query.get(node_id)
    if not node:
        flash("节点不存在", "warning")
        return redirect(url_for("index"))
    prev_node = Node.query.filter(
        Node.group_id == node.group_id,
        Node.sort_order < node.sort_order
    ).order_by(Node.sort_order.desc()).first()
    if prev_node:
        node.sort_order, prev_node.sort_order = prev_node.sort_order, node.sort_order
        db.session.commit()
    return redirect(url_for("index"))

# ---------------------------
# 向下移动节点
# ---------------------------
@app.route("/move_down/<int:node_id>")
@requires_auth
def move_down(node_id):
    node = Node.query.get(node_id)
    if not node:
        flash("节点不存在", "warning")
        return redirect(url_for("index"))
    next_node = Node.query.filter(
        Node.group_id == node.group_id,
        Node.sort_order > node.sort_order
    ).order_by(Node.sort_order.asc()).first()
    if next_node:
        node.sort_order, next_node.sort_order = next_node.sort_order, node.sort_order
        db.session.commit()
    return redirect(url_for("index"))

# ---------------------------
# 切换启用状态
# ---------------------------
@app.route("/toggle/<int:node_id>")
@requires_auth
def toggle_node(node_id):
    node = Node.query.get(node_id)
    if node:
        node.enabled = not node.enabled
        db.session.commit()
        try:
            update_nodes()
        except:
            pass
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# ---------------------------
# 编辑节点
# ---------------------------
@app.route("/edit/<int:node_id>", methods=["POST"])
@requires_auth
def edit_node(node_id):
    node = Node.query.get(node_id)
    if node:
        name = request.form.get("name", "").strip()
        link = request.form.get("link", "").strip()
        if name:
            node.name = name
        if link:
            node.link = re.sub(r"#.*$", "", link)
        db.session.commit()
        try:
            update_nodes()
        except:
            pass
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# ---------------------------
# 动态订阅
# ---------------------------
@app.route("/sub")
def sub():
    token = request.args.get("token", "")
    if token != get_token():
        abort(403, description="访问订阅需要正确的 token")
    nodes = Node.query.filter_by(enabled=True).order_by(Node.sort_order).all()
    out_links = []

    for n in nodes:
        link = n.link.strip()
        if link.startswith("vmess://"):
            try:
                raw = link[8:]
                decoded = base64.b64decode(raw + "==").decode()
                j = json.loads(decoded)
                j["ps"] = n.name
                new_raw = base64.b64encode(json.dumps(j).encode()).decode()
                out_links.append("vmess://" + new_raw)
            except:
                out_links.append(link)
        elif link.startswith("vless://"):
            clean = re.sub(r"#.*$", "", link)
            out_links.append(f"{clean}#{n.name}")
        else:
            clean = re.sub(r"#.*$", "", link)
            out_links.append(f"{clean}#{n.name}")

    sub_content = "\n".join(out_links)
    sub_b64 = base64.b64encode(sub_content.encode()).decode()
    return Response(sub_b64, mimetype="text/plain")

# ---------------------------
# 启动
# ---------------------------
if __name__ == "__main__":
    print(f"访问订阅链接时需要使用 token: {get_token()}")
    app.run(host="0.0.0.0", port=5786, debug=True)
