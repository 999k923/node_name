节点订阅管理器
==
实现多个代理/节点集中起来，通过一个域名提供统一订阅，客户端更新订阅就能获取所有节点。

支持一键部署，docker部署

轻量级节点管理系统，支持 TUIC/VLESS/VMess/Trojan/hy2等等节点统一管理方便域名订阅。
Web后台新增，修改，删除节点。

访问后台：`http://服务器IP:5786/`  
订阅地址：`http://您的IP:5786/sub?token=“TOKEN”`

<img width="1093" height="559" alt="image" src="https://github.com/user-attachments/assets/39618c3f-5aaf-4279-9c2f-443ea3b33ba2" />



## 功能
- Web后台增删改节点。
- 方便不同设备获取订阅后节点备名称会显示在客户端节点备注里面
- Ubuntu 一键部署
- docker compose部署

## 一键部署，自动完成。
```bash
git clone https://github.com/999k923/node_sub_manager.git && cd node_sub_manager && chmod +x deploy.sh run.sh stop.sh && ./deploy.sh
```

访问后台：`http://服务器IP:5786/`  
订阅地址：`http://您的IP:5786/sub?token=“TOKEN”`

## 注意
默认监听ipv4，如果需要监听ipv6端口需要把部署文件里面的监听改成监听ipv6后重启.
```bash
nano app.py
```
最后一行里面的
app.run(host="0.0.0.0", port=5786)改成 

app.run(host="::", port=5786)后重启生效



## 默认用户名密码

WEB_USER = "mimayoudianfuza"   

WEB_PASS = "zhendehenfuza"  

更改用户名密码编辑app.py文件，修改后重启生效
```bash
nano app.py
```

token安装时候随机生成，并记录在access_token.txt。
查看token
```bash
TOKEN=$(cat /root/node_sub_manager/access_token.txt)
echo "当前订阅 token: $TOKEN"
```
重启命令：
```bash
systemctl restart node_sub
```
停止：
```bash
./stop.sh
```
启动：
```bash
./run.sh
```
## 工具信息
reset_node_id.py节点删除之后序号不连贯，文件放到数据库一个文件目录，运行序号从新生成。


## 查看日志
```bash
journalctl -u node_sub -f
```

docker compose部署 
==
先创立好挂载的文件。
```bash
mkdir -p /opt/stacks/node/data
touch /opt/stacks/node/data/access_token.txt
touch /opt/stacks/node/data/nodes.db
```
手动先写入token内容
```bash
echo "你的token内容" > /opt/stacks/node/data/access_token.txt
```
开始部署docker了
```bash
version: "3.9"
services:
  node_name:
    image: 999k923/node_name:latest
    container_name: node_name
    restart: always
    ports:
      - 5786:5786
    volumes:
      - /opt/stacks/node/data/nodes.db:/app/instance/nodes.db
      - /opt/stacks/node/data/access_token.txt:/app/access_token.txt
    environment:
      - PYTHONUNBUFFERED=1
networks: {}
```
