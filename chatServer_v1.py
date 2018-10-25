import socketio
import eventlet
import random
import pandas
import pymysql
import json
from sqlalchemy import create_engine
pymysql.install_as_MySQLdb()

#实例化socketio实例化话对象
sio = socketio.Server()


# engine = create_engine('mysql://root:115113@localhost:3306/wade?charset=utf8')
# df = pandas.read_sql('company',engine)
# df = df.to_json()
# df = json.loads(df)
# df = df['nickname']
# name = [value for value in df.values()]

img = ['https://y.gtimg.cn/music/photo_new/T002R90x90M000002YiBgp4MWcKC.jpg?max_age=2592000',
        'https://y.gtimg.cn/music/photo_new/T002R90x90M0000035zusU4OF4IC.jpg?max_age=2592000',
        'https://y.gtimg.cn/music/photo_new/T002R300x300M000003jZVwO0G1s7d.jpg?max_age=2592000',
        'https://y.gtimg.cn/music/photo_new/T002R90x90M000002Pii1d05Ybic.jpg?max_age=2592000',
        'https://y.gtimg.cn/music/photo_new/T002R90x90M000002zRQ7N04x1Eq.jpg?max_age=2592000',
        'https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3199093078,918503307&fm=27&gp=0.jpg',
        'https://ss3.bdstatic.com/70cFv8Sh_Q1YnxGkpoWK1HF6hhy/it/u=2200166214,500725521&fm=27&gp=0.jpg',
        'https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3840425321,3671377620&fm=27&gp=0.jpg',
        'https://ss0.bdstatic.com/70cFuHSh_Q1YnxGkpoWK1HF6hhy/it/u=3045772323,1079911345&fm=27&gp=0.jpg',
        'https://ss2.bdstatic.com/70cFvnSh_Q1YnxGkpoWK1HF6hhy/it/u=875603750,1164694248&fm=11&gp=0.jpg'
        ]


conn = pymysql.connect(host='localhost',port= 3306,user = 'root',passwd='115113',db='socketio')
cur = conn.cursor()
sql = 'select * from user'
cur.execute(sql)
user =cur.fetchall()
user = list(user)

#凡是新的客户端连接上来，我就把它加入到clientList
userList = ['hello']
clientList = {
    'python': {'sid': 'python', 'name': 'python', 'isRoom': True, 'imgUrl': random.choice(user)[1]},
    'html5': {'sid': 'html5', 'name': 'html5', 'isRoom': True, 'imgUrl': random.choice(user)[1]}
}
# name = [
#     '小红','小奇','小黑','小何','小安','小明','小哈','小胖','小狗','小虾'
# ]


#@sio.on()监听什么事件
@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)
    if not hasattr(clientList,sid):#首先判断一下，之前这个连接还在不在，如果不在，那么这就是一个新的客户端，那么直接将这个客户端的SID直接作为key，所以下次想要获取客户端的信息，那么就可直接通过clientList[sid]
        if len(clientList)==2:
            clientList[sid] = {'sid':sid,'name':userList[-1],'isRoom':False,'imgUrl':random.choice(user)[1],'details':'这个人很懒，连说说都懒得发'}
        else:
            clientList[sid] = {'sid':sid,'name':random.choice(user)[0],'isRoom':False,'imgUrl':random.choice(user)[1],'details':'这个人很懒，连说说都懒得发'}
    # sio.emit('addChat',sid)
    sio.emit('updateClients',clientList) #广播给所有人当前的好友列表要更新
    sio.emit('emitID', clientList[sid], room=sid)  # 单独给这个新连接的客户发送它的sid
    sio.emit('login',user)

@sio.on('login')
def login(sid, data):
    print('login ', data)
    cur.execute('insert into user (name,img,password) values(%s,%s,%s)',(data['name'],random.choice(img),data['password']))
    conn.commit()
    sql = 'select * from user'
    cur.execute(sql)
    user =cur.fetchall()
    user = list(user)
    sio.emit('login',user)

@sio.on('sendUser')
def sendUser(sid,data):
    print('sendUser',data)
    userList.append(data)
    

#sendMessage这个事件，专门用于聊天
@sio.on('sendMessage')
def sendMessage(sid,data):
    #data  = { 'content':"聊天信息"，destId:'cd9ab3984c5b4ab5ba7bfa1dd027626f'，srcId:'ssgsdajgosidgjosadi'}
    print('sendMessage',data)
    # print(clientList)
    if (data['content']=='进入房间') or (data['content']=='离开房间'):
        pass
    else:
        cur.execute('insert into message (userName,content,friendName) values(%s,%s,%s)',(clientList[data['srcId']]['name'],data['content'],clientList[data['destId']]['name']))
        conn.commit()
    sio.emit('reply',data,room=data['destId'],skip_sid=data['srcId']) #将发送的数据，通过服务器转发给目标SID，skip_sid这个属性是用来忽视掉某个，如果是发群的话，那么会多发一次给自己，那么给群发的时候忽视掉自己
    sio.emit('reply', data, room=data['srcId']) #将发送的数据转发回给自己


#让某个客户端进入群（房间）
@sio.on('enterRoom')
def enterRoom(sid,data):
    sio.enter_room(sid,data['room'])
    info = {'content': '进入房间', 'destId': data['room'], 'srcId': sid}
    sio.emit('reply',info,room=data['room'])

#让某个客户端退出群（房间）
@sio.on('leaveRoom')
def leaveRoom(sid,data):
    sio.leave_room(sid,data['room'])
    info = {'content': '离开房间' ,'destId': sid, 'srcId': sid}
    sio.emit('reply', info, room=data['room'])

@sio.on('editUser')
def editUser(sid,data): #data = {'attrValue':'imgUrl','value':'用户需要修改的值'}
    clientList[sid][data['attrValue']]=data['value'] #修改sid用的是attrvalue携带的属性的值
    sio.emit('updateClients', clientList) #广播更新所有的客户端的在线列表
    sio.emit('emitID', clientList[sid], room=sid) #发送sid这个用户的个人信息给他


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)
    clientList.pop(sid) #如果客户端断开连接，那么将客户端从clientList客户端列表删除
    sio.emit('updateClients', clientList) #告诉前端更新一下，在线好友（客户端列表）
    

if __name__ == '__main__':
    # sio通过middleware转为应用服务
    app = socketio.Middleware(sio)

    # 依赖eventlet网关服务器
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
