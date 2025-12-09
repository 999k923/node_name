# 节点订阅管理器Node Subscription Manager
实现多个代理/节点集中起来，通过一个域名提供统一订阅，客户端更新订阅就能获取所有节点。

支持一键部署，docker部署

轻量级节点管理系统，支持 TUIC/VLESS/VMess/Trojan/hy2等等节点统一管理方便域名订阅。
Web后台新增，修改，删除节点。

访问后台：`http://服务器IP:5786/`  
订阅地址：`http://您的IP:5786/sub?token=“TOKEN”`

<img width="1012" height="680" alt="image" src="https://github.com/user-attachments/assets/48df43a8-beb6-4af2-9eac-78d828a51d29" />



## 功能
- Web后台增删改节点。
- 方便不同设备获取订阅后节点备名称会显示在客户端节点备注里面
- Ubuntu 一键部署
- docker compose部署

## 一键部署，自动完成。
```bash
git clone https://github.com/999k923/node_name.git && cd node_name && chmod +x deploy.sh run.sh stop.sh && ./deploy.sh
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

