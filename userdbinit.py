#coding:utf-8
import pickle
import random

userdb_name = 'userdb.dat'

def get_db():
    with open(userdb_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(userdb_name,'w') as f:
        pickle.dump(db,f)
       

print(u'すべてのユーザデータベースが***初期化***されます.よろしいですか? 適切なオペレーション権限は有りますか?')
print(u'もしあるならば,"InitAuthorized" と入力してください')
check = raw_input(u'> ')
if not check == 'InitAuthorized':
    exit()
    
userlist = list()

usernum = 6000
for i in xrange(1000,usernum):
    userid = str(i)
    password = str(random.randint(100,999))
    username = 'USER'
    score = 0
    visible = True
    
    userlist.append({'id':userid, 'pass':password, 'name':username, 'score':score, 'v':visible})
    
set_db(userlist)
print(u'{}ユーザ 作成完了'.format(len(userlist)))