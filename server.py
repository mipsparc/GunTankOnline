#coding:utf-8
#default:port5000でlisten
from flask import Flask
from flask import request
import pickle
import time
import json
import random

pickledb_name = 'pickledb.dat'
app = Flask(__name__)

tank_list = [
    {
    'tank_speed':400,
    'bullet_speed':900,
    'bullet_damage':20,
    'hp':600,
    'bullet_per_sec':4},
    {
    'tank_speed':350,
    'bullet_speed':500,
    'bullet_damage':30,
    'hp':750,
    'bullet_per_sec':1.7},
    {
    'tank_speed':300,
    'bullet_speed':450,
    'bullet_damage':40,
    'hp':900,
    'bullet_per_sec':1.5}]

def get_db():
    with open(pickledb_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(pickledb_name,'w') as f:
        pickle.dump(db,f)

@app.route('/time')
def give_time():
    return str(time.time())

@app.route('/add_wait')
def add_wait():
    user_id = request.args['id']
    password = request.args['pass']
    tank_id = int(request.args['tank_id'])
    wait_id = str(random.randint(1,99999999))
    ip_addr = request.args['ipaddr']
    print ip_addr
    db = get_db()
    for user in db['user_list']:
        if user['user_id'] == user_id and user['pass'] == password:
            db['wait_list'].append({'user_id':user_id,'score':user['score'],'tank_id':tank_id,'wait_id':wait_id,'ip_addr':ip_addr,'time':time.time()})
            set_db(db)
            return wait_id
    return 'error'

@app.route('/check_start')
def check_start():
    wait_id = request.args['wait_id']
    db = get_db()
    for start in db['start_list']:
        for user in start[0]:
            if wait_id == user['wait_id'] :
                return json.dumps({'users':start,'data':tank_list})
    return 'waiting'
    
app.run('0.0.0.0',debug=True)
