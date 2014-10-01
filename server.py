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

db_name = 'userdb.dat'
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

@app.route('/time')
def give_time():
    return json.dumps([str(time.time()), request.remote_addr])

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
    user_id = data.get('user_id')
    password = data.get('password')

    session_id = random.randint(1,99999999)
    
    if db['wait_for_start'] and db['start_time'] <= time.time():
        print('cleared waitlist')
        db['wait_for_start'] = False
        db['battle_id'] = random.randint(1,99999999)
        db['start_time'] = None
        db['waitlist'] = list()
    
    db['waitlist'].append({'ipaddr':ipaddr, 'port':port, 'tank_id':tank_id, 'session_id':session_id, 'score':-1})
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
    set_db(db)
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
