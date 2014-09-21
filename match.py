#coding:utf-8
import pickle
from maze_generator import Maze
from random import randint

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
        
#TODO def init_place()

if __name__ == "__main__":
    db = get_db()
    wait_num = len(db['wait_list'])
    if wait_num < 2:
        match_num_list = [0,]
    elif wait_num == 2:
        match_num_list = [0,1]
    elif wait_num == 3:
        match_num_list = [0,1]
    elif wait_num >= 4:
        match_num_list = [1,]

    if not wait_num < 2:
        db['wait_list'].sort(key=lambda x:x['score'])
        players_num_list = list()
        carry = wait_num % max(match_num_list)
        players_for_match = wait_num / max(match_num_list)
        #人数配分
        while wait_num:
            wait_num -= players_for_match
            if wait_num and wait_num < players_for_match:
                players_for_match += carry
            players_num_list.append(players_for_match)

        for players_num in players_num_list:
            maze = Maze(maze_x, maze_y).__str__()
            match_players = db['wait_list'][0:players_num]
            db['start_list'].append([match_players,maze])
            del db['wait_list'][0:players_num]
        
        set_db(db)

        print("{}players matched".format(wait_num))
    print("No player matched({} waiting)".format(wait_num))