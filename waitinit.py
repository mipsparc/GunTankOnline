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
        
print(u'待機データがクリアされます.よろしいですか? 適切なオペレーション権限は有りますか?')
check = raw_input(u'Yes/No> ')
if not check == 'Yes':
    exit()

db = get_db()
db['waitlist'] = list()
set_db(db)
print(u'待機データ クリア完了')