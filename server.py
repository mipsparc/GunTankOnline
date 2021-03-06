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

db_name = 'db.dat'

app = Flask(__name__)

maze_x = 10
maze_y = 10

stage_list = list()

for i in range(20):
    with open('stage/stage{}.txt'.format(i)) as f:
        stage_list.append(f.read())

tank_dataset = [
    {
    'tank_speed':500.0,
    'bullet_speed':900.0,
    'bullet_damage':20,
    'hp':600,
    'bullet_per_sec':3,
    'accel_ratio':250,
    'brake_ratio':0.7},
    {
    'tank_speed':300.0,
    'bullet_speed':900.0,
    'bullet_damage':30,
    'hp':700,
    'bullet_per_sec':3,
    'accel_ratio':150,
    'brake_ratio':0.5},
    {
    'tank_speed':400.0,
    'bullet_speed':1600.0,
    'bullet_damage':40,
    'hp':400,
    'bullet_per_sec':2,
    'accel_ratio':200,
    'brake_ratio':0.5},
    {
    'tank_speed':450.0,
    'bullet_speed':900.0,
    'bullet_damage':15,
    'hp':350,
    'bullet_per_sec':10,
    'accel_ratio':500,
    'brake_ratio':0.9},
    {
    'tank_speed':750.0,
    'bullet_speed':900.0,
    'bullet_damage':10,
    'hp':450,
    'bullet_per_sec':4,
    'accel_ratio':700,
    'brake_ratio':0.5},
    {
    'tank_speed':600.0,
    'bullet_speed':450.0,
    'bullet_damage':30,
    'hp':600,
    'bullet_per_sec':2,
    'accel_ratio':600,
    'brake_ratio':0.4}]
    
    
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
#json:ipaddr,port,tank_id
@app.route('/attend')
def attend():
    db = get_db()
    data = json.loads(request.args['json'])
    ipaddr = data['ipaddr']
    port = data['port']
    tank_id = data['tank_id']
    name = 'GUEST{}'.format(len(db['waitlist']))

    session_id = random.randint(1,99999999)
    
    #新規バトル待機開始
    if db['start_time'] <= time.time():
        print('cleared waitlist')
        db['wait_for_start'] = False
        db['battle_id'] = random.randint(1,99999999)
        db['start_time'] = 2147483647   #max unixtime
        db['waitlist'] = list()
        db['battles'] += 1
        
    db['connection'] +=1
    
    #未アップロードのscoreは-1
    db['waitlist'].append({'ipaddr':ipaddr, 'port':port, 'tank_id':tank_id,
                           'name':name,'session_id':session_id, 'score':-1})
    set_db(db)
    
    return json.dumps({'session_id':session_id,'name':name})

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
        db['start_time'] = time.time() + 30
        
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
        #3番めはclosedフラグ
        db['battlelist'][battle_id] = [stage, db['waitlist'], False]
        set_db(db)
    
    return json.dumps(db['battlelist'][battle_id]+[tank_dataset])

#スコアを報告
#query: battle_id, session_id, score, deadtime
@app.route('/score')
def score():
    battle_id = request.args['battle_id']
    session_id = int(request.args['session_id'])
    score = int(request.args['score'])
    alivetime = float(request.args['alivetime'])
    db = get_db()
    for i,session in  enumerate(db['battlelist'][battle_id][1]):
        if session['session_id'] == session_id:
            db['battlelist'][battle_id][1][i]['score'] = score
            db['battlelist'][battle_id][1][i]['alivetime'] = alivetime
            
    set_db(db)

    
    return ''
    
#ランキング取得
#query: battle_id
@app.route('/ranking')
def ranking():
    db = get_db()
    battle_id = request.args['battle_id']
    #closedしてない(初回アクセス時)
    if not db['battlelist'][battle_id][2]:
        db['battlelist'][battle_id][2] = True
    set_db(db)

    return json.dumps(db['battlelist'][battle_id][1])

#tank_dataset を返す
@app.route('/tankdata')
def tankdata():
    return json.dumps(tank_dataset)
    
    
app.run('0.0.0.0',debug=True)
