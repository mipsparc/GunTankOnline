#coding:utf-8
import pickle

db_name = 'userdb.dat'

def get_db():
    with open(db_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(db_name,'w') as f:
        pickle.dump(db,f)
        
set_db({'waitlist':list(), 'battlelist':dict(), 'wait_for_start':False, 'start_time':0, 'battle_id':0})
print('DB Initalized')