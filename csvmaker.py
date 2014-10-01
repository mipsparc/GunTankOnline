import csv
import pickle

userdb_name = 'userdb.dat'
csv_name = 'userlist.csv'

def get_db():
    with open(userdb_name,'r') as f:
        db = pickle.load(f)
    return db

userlist = get_db()

with open(csv_name, 'w') as f:
    writer = csv.writer(f)
    for user in userlist:
        userid = user['id']
        password = user['pass']
        writer.writerow((userid, password))