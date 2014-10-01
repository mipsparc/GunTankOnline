#coding:utf-8
#default:port5000でlisten
#list:waitlist
#dict:battlelist
#bool:wait_for_start
#int:start_time,battle_id
from flask import Flask
from flask import request
import pickle
import time
import datetime
import json
import random
from maze_generator import Maze

db_name = 'db.dat'
userdb_name = 'userdb.dat'
app = Flask(__name__)

maze_x = 10
maze_y = 10

stage_list = list()

for i in range(20):
    with open('stage/stage{}.txt'.format(i)) as f:
        stage_list.append(f.read())

tank_dataset = [
    {
    'tank_speed':400.0,
    'bullet_speed':900.0,
    'bullet_damage':20,
    'hp':600,
    'bullet_per_sec':4,
    'accel_ratio':300,
    'brake_ratio':0.7},
    {
    'tank_speed':200.0,
    'bullet_speed':900.0,
    'bullet_damage':40,
    'hp':800,
    'bullet_per_sec':2,
    'accel_ratio':200,
    'brake_ratio':0.7},
    {
    'tank_speed':600.0,
    'bullet_speed':900.0,
    'bullet_damage':15,
    'hp':400,
    'bullet_per_sec':6,
    'accel_ratio':300,
    'brake_ratio':0.7},
    {
    'tank_speed':600.0,
    'bullet_speed':900.0,
    'bullet_damage':15,
    'hp':400,
    'bullet_per_sec':6,
    'accel_ratio':300,
    'brake_ratio':0.7},
    {
    'tank_speed':600.0,
    'bullet_speed':900.0,
    'bullet_damage':15,
    'hp':400,
    'bullet_per_sec':6,
    'accel_ratio':300,
    'brake_ratio':0.7},
    {
    'tank_speed':600.0,
    'bullet_speed':900.0,
    'bullet_damage':15,
    'hp':400,
    'bullet_per_sec':6,
    'accel_ratio':300,
    'brake_ratio':0.7}]
    
    
def get_db():
    with open(db_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(db_name,'w') as f:
        pickle.dump(db,f)
        
def get_userdb():
    with open(userdb_name,'r') as f:
        db = pickle.load(f)
    return db

def set_userdb(db):
    with open(userdb_name,'w') as f:
        pickle.dump(db,f)
        
def auth(userid, password):
    users = get_userdb()
    for user in users:
        if user['id'] == userid and user['pass'] == password:
            return True
    #auth fail
    return False

def get_userdata(userid):
    users = get_userdb()
    for user in users:
        if user['id'] == userid:
            return [user['name'],user['score']]
    #fail
    return False

@app.route('/time')
def give_time():
    return json.dumps([str(time.time()), request.remote_addr])

#ユーザ認証して,データ返す
@app.route('/user')
def userdata():
    user_id = request.args['id']
    password = request.args['pass']
    if not auth(user_id, password):
        return json.dumps({'auth':False})
    else:
        return json.dumps({'auth':True,'userdat':get_userdata(user_id)})

#参戦
#query:json
#json:ipaddr,port,tank_id,[user_id,password]
@app.route('/attend')
def attend():
    db = get_db()
    data = json.loads(request.args['json'])
    ipaddr = data['ipaddr']
    port = data['port']
    tank_id = data['tank_id']
    user_id = data.get('id')
    password = data.get('pass')
    if user_id and password:
        if not auth(user_id, password):
            #認証失敗時は0を返す
            return json.dumps({'session_id':0})
        name, score = get_userdata(user_id)

    else:
        name = None

    session_id = random.randint(1,99999999)
    
    if db['start_time'] <= time.time():
        print('cleared waitlist')
        db['wait_for_start'] = False
        db['battle_id'] = random.randint(1,99999999)
        db['start_time'] = 2147483647   #max unixtime
        db['waitlist'] = list()
    
    #未アップロードのscoreは-1
    db['waitlist'].append({'ipaddr':ipaddr, 'port':port, 'tank_id':tank_id,
                           'id':user_id,'name':name,'session_id':session_id, 'score':-1})
    set_db(db)
    
    return json.dumps({'session_id':session_id})

#待機人数と開始時刻の確認
@app.route('/check')
def check():
    db = get_db()
    waiting = len(db['waitlist'])
    #試合時間設定
    battle_duration = 180
    if not db['wait_for_start'] and waiting >= 2:
        db['wait_for_start'] = True
        #開始時刻設定
        db['start_time'] = time.time() + 10
        
        set_db(db)

    return json.dumps({'start':db['wait_for_start'], 'waiting':waiting, 'start_time':db['start_time'], 'battle_id':db['battle_id'],'duration':battle_duration})

#query:battle_id
@app.route('/start')
def start():
    db = get_db()
    battle_id = request.args['battle_id']
    #そのバトルが初回アクセス時
    if not battle_id in db['battlelist']:
        stage = random.choice(stage_list)
        db['battlelist'][battle_id] = [stage, db['waitlist']]
        set_db(db)
    
    return json.dumps(db['battlelist'][battle_id]+[tank_dataset])

#スコアを報告
#query: battle_id, session_id, score
@app.route('/score')
def score():
    battle_id = request.args['battle_id']
    session_id = int(request.args['session_id'])
    score = int(request.args['score'])
    db = get_db()
    for i,session in  enumerate(db['battlelist'][battle_id][1]):
        if session['session_id'] == session_id:
            db['battlelist'][battle_id][1][i]['score'] = score
            userid = db['battlelist'][battle_id][1][i]['id']
    set_db(db)
    
    #スコアをユーザの時は記録
    if userid:
        users = get_userdb()
        for i,user in enumerate(users):
            if users[i]['id'] == userid:
                users[i]['score'] += score
        set_userdb(users)
    
    return ''
    
#ランキング取得
#query: battle_id
@app.route('/ranking')
def ranking():
    db = get_db()
    battle_id = request.args['battle_id']
    return json.dumps(db['battlelist'][battle_id][1])

#tank_dataset を返す
@app.route('/tankdata')
def tankdata():
    return json.dumps(tank_dataset)
    
    
app.run('0.0.0.0',debug=True)
