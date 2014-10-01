#coding:utf-8
import pickle

db_name = 'db.dat'

def get_db():
    with open(db_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(db_name,'w') as f:
        pickle.dump(db,f)
        
print(u'すべての試合管理データベースが***初期化***されます.よろしいですか? 適切なオペレーション権限は有りますか?')
print(u'もしあるならば,Authorized と入力してください')
check = raw_input(u'> ')
if not check == 'Authorized':
    exit()

set_db({'waitlist':list(),
        'battlelist':dict(),
        'wait_for_start':False,
        'start_time':0,
        'battle_id':0,})
print(u'試合管理データベース 初期化完了')