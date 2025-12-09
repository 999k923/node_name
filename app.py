from flask import Flask, Response, render_template, request, redirect, url_for, flash, abort
from models import db, Node, SubscriptionGroup
import base64
import os
import re
import string
import random
from functools import wraps
import requests
from update_node_name import update_nodes  # 安全导入，无循环依赖

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nodes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret_key_for_flash"
db.init_app(app)

with app.app_context():
    if not os.path.exists("nodes.db"):
        db.create_all()

# ---------------------------
# Token 生成/读取
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
# Web 后台用户名密码
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
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# 节点重排函数
# ---------------------------
def reorder_group_nodes(group_id):
    nodes = Node.query.filter_by(group_id=group_id).order_by(Node.sort_order).all()
    for i, node in enumerate(nodes, start=1):
        node.sort_order = i
    db.session.commit()

# ---------------------------
# Web管理后台
# ---------------------------
@app.route("/")
@requires_auth
def index():
    nodes = Node.query.order_by(Node.sort_order).all()
    groups = SubscriptionGroup.query.all()
    token = get_token()
    return render_template("index.html", nodes=nodes, groups=groups, token=token)

# 添加单个节点
@app.route("/add", methods=["POST"])
@requires_auth
def add_node():
    name = request.form.get("name", "").strip()
    link = request.form.get("link", "").strip()
    link = re.sub(r"#.*$", "", link)

    if name and link:
        node = Node(name=name, link=link, sort_order=Node.query.count()+1)
        try:
            db.session.add(node)
            db.session.commit()
            try:
                update_nodes()
            except Exception as e:
                print(f"update_nodes 出错: {e}")
        except Exception as e:
            db.session.rollback()
            flash(f"添加节点失败: {e}", "danger")
    else:
        flash("节点名称或链接不能为空", "warning")
    return redirect(url_for("index"))

# 编辑节点
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
        try:
            db.session.commit()
            try:
                update_nodes()
            except Exception as e:
                print(f"update_nodes 出错: {e}")
        except Exception as e:
            db.session.rollback()
            flash(f"编辑节点失败: {e}", "danger")
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# 删除节点
@app.route("/delete/<int:node_id>")
@requires_auth
def delete_node(node_id):
    node = Node.query.get(node_id)
    if node:
        group_id = node.group_id
        try:
            db.session.delete(node)
            db.session.commit()
            if group_id:
                reorder_group_nodes(group_id)
        except Exception as e:
            db.session.rollback()
            flash(f"删除节点失败: {e}", "danger")
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# 切换节点状态
@app.route("/toggle/<int:node_id>")
@requires_auth
def toggle_node(node_id):
    node = Node.query.get(node_id)
    if node:
        try:
            node.enabled = not node.enabled
            db.session.commit()
            try:
                update_nodes()
            except Exception as e:
                print(f"update_nodes 出错: {e}")
        except Exception as e:
            db.session.rollback()
            flash(f"切换节点状态失败: {e}", "danger")
    else:
        flash("节点不存在", "warning")
    return redirect(url_for("index"))

# ---------------------------
# 订阅集合导入
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
        r.raise_for_status()
        content_b64 = r.text.strip()
        content = base64.b64decode(content_b64).decode()
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        group = SubscriptionGroup(url=sub_url)
        db.session.add(group)
        db.session.commit()

        for i, line in enumerate(lines, start=1):
            n = Node(name=f"节点{i}", link=line, enabled=True, group_id=group.id, sort_order=i)
            db.session.add(n)
        db.session.commit()
        flash(f"订阅导入成功，共 {len(lines)} 个节点", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"导入失败: {e}", "danger")
    return redirect(url_for("index"))

# 删除订阅集合及其节点
@app.route("/delete_group/<int:group_id>")
@requires_auth
def delete_group(group_id):
    group = SubscriptionGroup.query.get(group_id)
    if group:
        try:
            Node.query.filter_by(group_id=group.id).delete()
            db.session.delete(group)
            db.session.commit()
            flash("订阅集合及其节点已删除", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"删除失败: {e}", "danger")
    else:
        flash("订阅集合不存在", "warning")
    return redirect(url_for("index"))

# 节点上下移动
@app.route("/move_up/<int:node_id>")
@requires_auth
def move_up(node_id):
    node = Node.query.get(node_id)
    if node and node.group_id:
        prev_node = Node.query.filter_by(group_id=node.group_id)\
            .filter(Node.sort_order < node.sort_order)\
            .order_by(Node.sort_order.desc()).first()
        if prev_node:
            node.sort_order, prev_node.sort_order = prev_node.sort_order, node.sort_order
            db.session.commit()
    return redirect(url_for("index"))

@app.route("/move_down/<int:node_id>")
@requires_auth
def move_down(node_id):
    node = Node.query.get(node_id)
    if node and node.group_id:
        next_node = Node.query.filter_by(group_id=node.group_id)\
            .filter(Node.sort_order > node.sort_order)\
            .order_by(Node.sort_order).first()
        if next_node:
            node.sort_order, next_node.sort_order = next_node.sort_order, node.sort_order
            db.session.commit()
    return redirect(url_for("index"))

# ---------------------------
# 动态订阅输出
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
            import json
            try:
                raw = link[8:]
                decoded = base64.b64decode(raw + "==").decode()
                j = json.loads(decoded)
                j["ps"] = n.name
                new_raw = base64.b64encode(json.dumps(j).encode()).decode()
                out_links.append("vmess://" + new_raw)
            except Exception as e:
                out_links.append(link)
            continue

        elif link.startswith("vless://"):
            clean = re.sub(r"#.*$", "", link)
            out_links.append(f"{clean}#{n.name}")
            continue

        else:
            clean = re.sub(r"#.*$", "", link)
            out_links.append(f"{clean}#{n.name}")

    sub_content = "\n".join(out_links)
    sub_b64 = base64.b64encode(sub_content.encode()).decode()
    return Response(sub_b64, mimetype="text/plain")

if __name__ == "__main__":
    print(f"访问订阅链接时需要使用 token: {get_token()}")
    app.run(host="0.0.0.0", port=5786, debug=True)
