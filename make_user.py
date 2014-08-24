#coding:utf-8
import pickle
from random import randint

with open('pickledb.dat') as f:
    db = pickle.load(f)

new_user_list = list()
user_list = list()
for num in range(100):
    user_id = str(randint(10000,99999))
    if not user_id in user_list:
        password = str(randint(10000,99999))
        db['user_list'].append({'score':0,'user_id':user_id,'screen_name':user_id,'pass':password,'kill_count':0})
        new_user_list.append({'user_id':user_id,'password':password})

with open('pickledb.dat','w') as f:
    pickle.dump(db,f)

with open('out.txt','w') as f:
    for new_user in new_user_list:
        f.write('ID: '+new_user['user_id']+' PASSWORD:'+new_user['password']+'\n')

