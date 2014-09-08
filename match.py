#coding:utf-8
import pickle
from maze_generator import Maze

pickledb_name = 'pickledb.dat'
maze_x = 10
maze_y = 10

def get_db():
    with open(pickledb_name,'r') as f:
        db = pickle.load(f)
    return db

def set_db(db):
    with open(pickledb_name,'w') as f:
        pickle.dump(db,f)

db = get_db()
wait_num = len(db['wait_list'])

if wait_num > 2:
    maze = Maze(maze_x, maze_y).__str__()
    match_players = db['wait_list']
    db['start_list'].append([match_players,maze])
    db['wait_list'] = list()
    
    set_db(db)

print('{}players matched'.format(wait_num))