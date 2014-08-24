#coding:utf-8
import pygame
from pygame.locals import *
import socket
import json
from multiprocessing import Process,Queue
import time
import random
import urllib2
from textbox import TextBox, Button


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, way, speed, bullet_speed, bullet_per_sec,
            hp, bullet_damage, tank_id, center=None):
        #setting sprite group
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.clock = pygame.time.Clock()
        self.clock.tick()

        self.center = center

        self.origin_image = pygame.image.load(tank_id_file[tank_id]).convert_alpha()
        self.width = self.origin_image.get_width()
        self.height = self.origin_image.get_height()
        self.rect = self.origin_image.get_rect()

        self.hp = hp
        self.way = way
        self.speed = speed
        self.bullet_speed = bullet_speed
        self.bullet_per_sec = bullet_per_sec
        self.bullet_damage = bullet_damage
        self.tank_id = tank_id

        self.up_image = pygame.transform.rotate(self.origin_image, 270)
        self.right_image = pygame.transform.rotate(self.origin_image, 180)
        self.down_image = pygame.transform.rotate(self.origin_image, 90)
        self.image = self.origin_image

        self.bullet_passed_sec = 0

        if self.center:
            #背景を動かすときの相対的な座標
            self.relative_x = -screen_width/2 + wall_height
            self.relative_y = -screen_height/2 + wall_height + wall_width
            self.rect.x = x
            self.rect.y = y

        else:
            self.default_x = x
            self.default_y = y

    def update(self, relative_x=None, relative_y=None):
        if self.center:
            passed_seconds = self.clock.tick()/1000.0

            x_diff = 0
            y_diff = 0

            pygame.event.pump()
            pressed_keys = pygame.key.get_pressed()
            last_way = self.way
            if pressed_keys[K_UP] or pressed_keys[K_w]:
                self.way = 'up'
                y_diff = -self.speed * passed_seconds
            elif pressed_keys[K_DOWN] or pressed_keys[K_s]:
                self.way = 'down'
                y_diff = self.speed * passed_seconds
            elif pressed_keys[K_LEFT] or pressed_keys[K_a]:
                self.way = 'left'
                x_diff = -self.speed * passed_seconds
            elif pressed_keys[K_RIGHT] or pressed_keys[K_d]:
                self.way = 'right'
                x_diff = self.speed * passed_seconds

            #方向固定
            if pressed_keys[K_z]:
                self.way = last_way
                if self.way == 'up' or self.way == 'down':
                    x_diff = 0
                elif self.way == 'left' or self.way == 'right':
                    y_diff = 0

            self.bullet_passed_sec += passed_seconds
            if pressed_keys[K_SPACE] and \
                    self.bullet_passed_sec * self.bullet_per_sec >= 1:
                if x_diff or y_diff:
                    self.fire(self.speed + self.bullet_speed)
                else:
                    self.fire(self.bullet_speed)
                self.bullet_passed_sec = 0

            self.relative_x += x_diff
            self.relative_y += y_diff
            self.x = self.relative_x + screen_width/2
            self.y = self.relative_y + screen_height/2

        else:
            self.rect.x = self.default_x - relative_x
            self.rect.y = self.default_y - relative_y

        #自機上下左右に応じて画像差し替え
        if self.way == 'up':
            self.image = self.up_image
        elif self.way == 'down':
            self.image = self.down_image
        elif self.way == 'left':
            self.image = self.origin_image
        elif self.way == 'right':
            self.image = self.right_image

    def fire(self, speed, bullet_id=None):
        if self.center:
            bullet_id = random.randint(1, 99999999)
            Bullet(self, speed, bullet_id, self.bullet_damage)
            send_queue.put({
                'ipaddr_list':ipaddr_list,
                'type':'fire',
                'time':time.time(),
                'x':self.x,
                'y':self.y,
                'way':self.way,
                'bullet_id':bullet_id,
                'speed':speed
                })
        else:
            Bullet(self, speed,bullet_id, self.bullet_damage)

    def struck(self, bullet_damage):
        self.hp -= bullet_damage


class Bullet(pygame.sprite.Sprite):
    def __init__(self, tank, speed, bullet_id, bullet_damage):
        self.tank = tank
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.clock = pygame.time.Clock()
        self.clock.tick()

        self.bullet_id = bullet_id
        self.bullet_damage = bullet_damage

        self.origin_image = pygame.image.load(bullet_id_file[self.tank.tank_id]).convert_alpha()

        if tank.way == 'up':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width/2
                self.default_y = screen_height/2 + tank.relative_y
            else:
                self.default_x = tank.default_x + tank.width/2
                self.default_y = tank.default_y
            self.image = pygame.transform.rotate(self.origin_image, 90)
        elif tank.way == 'down':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width/2
                self.default_y = screen_height/2 + tank.relative_y + tank.width
            else:
                self.default_x = tank.default_x + tank.width/2
                self.default_y = tank.default_y + tank.width
            self.image = pygame.transform.rotate(self.origin_image, 270)
        elif tank.way == 'left':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x
                self.default_y = screen_height/2 + tank.relative_y + tank.height/2
            else:
                self.default_x = tank.default_x
                self.default_y = tank.default_y + tank.height/2
            self.image = pygame.transform.rotate(self.origin_image, 180)
        elif tank.way == 'right':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width
                self.default_y = screen_height/2 + tank.relative_y + tank.height/2
            else:
                self.default_x = tank.default_x + tank.width
                self.default_y = tank.default_y + tank.height/2
            self.image = self.origin_image

        self.rect = self.image.get_rect()
        self.way = tank.way
        self.speed = speed
        
        if tank.center:
            self.rect.x = self.default_x - tank.relative_x
            self.rect.y = self.default_y - tank.relative_y
        else:
            self.rect.x = self.default_x - mytank.relative_x
            self.rect.y = self.default_y - mytank.relative_y

    def update(self, relative_x, relative_y):
        passed_seconds = self.clock.tick()/1000.0

        if self.way == 'up':
            self.default_y -= self.speed * passed_seconds
        elif self.way == 'down':
            self.default_y += self.speed * passed_seconds
        elif self.way == 'left':
            self.default_x -= self.speed * passed_seconds
        elif self.way == 'right':
            self.default_x += self.speed * passed_seconds

        #固定objとの衝突時
        if pygame.sprite.spritecollideany(self, walls):
            bullets.remove(self)
            all_sprites.remove(self)
        #自機に衝突時
        if not self.tank.center and pygame.sprite.collide_rect(self, mytank):
            mytank.struck(self.bullet_damage)
            bullets.remove(self)
            all_sprites.remove(self)
            send_queue.put({
                    'ipaddr_list':ipaddr_list,
                    'type':'struck',
                    'bullet_id':self.bullet_id,
                    'hp':mytank.hp
                    })
        #衝突した弾を削除
        if self.bullet_id in struckted_bullet_list:
            bullets.remove(self)
            all_sprites.remove(self)

        self.rect.x = self.default_x - relative_x
        self.rect.y = self.default_y - relative_y


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, way):
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.get_img()
        if way == 'landscape':
            self.image = self.wall_landscape
        elif way == 'portrait':
            self.image = self.wall_portrait

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.default_x = x
        self.default_y = y

    def update(self, relative_x, relative_y):
        self.rect.x = self.default_x - relative_x
        self.rect.y = self.default_y - relative_y

    def get_img(self):
        self.wall_landscape = pygame.image.load('./imgs/wall.png').convert()
        self.wall_portrait = pygame.transform.rotate(self.wall_landscape, 90)


class OuterWall(Wall):
    def get_img(self):
        self.wall_landscape = pygame.image.load('./imgs/outer_wall.png').convert()
        self.wall_portrait = pygame.transform.rotate(self.wall_landscape, 90)


class Adapter(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.get_img()

        self.image = self.adapter_image
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.default_x = x
        self.default_y = y

    def update(self, relative_x, relative_y):
        self.rect.x = self.default_x - relative_x
        self.rect.y = self.default_y - relative_y

    def get_img(self):
        self.adapter_image = pygame.image.load('./imgs/adapter.png').convert()


class OuterAdapter(Adapter):
    def get_img(self):
        self.adapter_image = pygame.image.load('./imgs/outer_adapter.png').convert()


def make_field(maze, wall_width, wall_height, adapter_width, adapter_height):
    maze_x = 10
    maze_y = 10
    field_x = (wall_width + wall_height) * maze_x - wall_height
    field_y = (wall_width + wall_height) * maze_y - wall_height
    #maze = Maze(maze_x, maze_y).__str__()
    current_x = 0
    current_y = 0
    maze_lines = maze.split('\n')
    for line_num, line in enumerate(maze_lines):
        line.strip()
        for s_num, s in enumerate(line):
            outer_line = False
            outer_char = False
            if s_num == 0 or s_num == len(line) - 1:
                outer_char = True
            if line_num == len(maze_lines)-2 or line_num == 0:
                outer_line = True

            if s == ' ':
                current_x += wall_width
            elif s == '_':
                if not(outer_char or outer_line):
                    Wall(current_x, current_y + wall_width, 'landscape')
                else:
                    OuterWall(current_x, current_y + wall_width, 'landscape')
                current_x += wall_width
            elif s == '.':
                if not(outer_char or outer_line):
                    Adapter(current_x, current_y + wall_width)
                else:
                    OuterAdapter(current_x, current_y + wall_width)
                current_x += wall_height
            elif s == '|':
                if not outer_char:
                    Wall(current_x, current_y, 'portrait')
                    Adapter(current_x, current_y + wall_width)
                    current_x += wall_height
                else:
                    OuterWall(current_x, current_y, 'portrait')
                    OuterAdapter(current_x, current_y + wall_width)
                    current_x += wall_height

        current_x = 0
        current_y += wall_width


#
#転送周り
def send(send_queue, send_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            while not send_queue.empty():
                send_data = send_queue.get(block=False)
                for ipaddr in send_data['ipaddr_list']:
                    sock.sendto(json.dumps(send_data), (ipaddr, send_port))
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass

def receive(receive_queue, receive_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('',receive_port))

        while True:
            data, addr = sock.recvfrom(4096)
            ipaddr, recv_port = addr
            receive_queue.put((json.loads(data),ipaddr))
    except KeyboardInterrupt:
        pass

#敵が動いた時に更新
def enemy_move(receive_data, ipaddr):
    for enemy in enemy_list:
        if enemy['ipaddr'] == ipaddr:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']

#敵が発射した時に初期位置と方向,弾IDをリストに追加
def enemy_fire(receive_data, ipaddr):
    for enemy in enemy_list:
        if enemy['ipaddr'] == ipaddr:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']
            enemy['obj'].fire(receive_data['speed'],receive_data['bullet_id'])

#敵が被弾したと申告してきた時にHPを合わせて,弾IDを削除リストに追加
def enemy_struck(receive_data, ipaddr):
    for enemy in enemy_list:
        if enemy['ipaddr'] == ipaddr:
            enemy['obj'].hp = receive_data['hp']
    struckted_bullet_list.append(receive_data['bullet_id'])
    

if __name__ == '__main__':
    server_addr = '192.168.3.4:5000'
    #proxy対策
    my_ipaddr = raw_input('MyIPaddr> ')
    
    if my_ipaddr=='localhost':
        my_ipaddr = '127.0.0.1'
        server_ipaddr = '127.0.0.1:5000'
        send_port = int(raw_input('SEND PORT> '))
        receive_port = int(raw_input('RECV PORT> '))
    else:
        send_port = 8800
        receive_port = 8800
    
    screen_width = 1024
    screen_height = 768
    #tank_idに対応したファイル名
    tank_id_file = ('./imgs/0_tank.png','./imgs/1_tank.png','./imgs/2_tank.png','./imgs/3_tank.png')
    bullet_id_file = ('./imgs/0_bullet.png','./imgs/1_bullet.png',
                      './imgs/2_bullet.png','./imgs/3_bullet.png')
    
    
    pygame.init()
    screen = pygame.display.set_mode([screen_width, screen_height])

    pygame.display.set_caption('GTO -Gun Tank Online-')
    clock = pygame.time.Clock()

    #削除する弾リスト
    struckted_bullet_list = list()

    wall_width = pygame.image.load('./imgs/wall.png').get_width()
    wall_height = pygame.image.load('./imgs/wall.png').get_height()
    adapter_height = pygame.image.load('./imgs/adapter.png').get_height()
    adapter_width = pygame.image.load('./imgs/adapter.png').get_width()

    #TODO グラフィック番号変更可能に
    #戦車のグラフィック番号
    tank_id = 0
    
    #送受信データキュー,送受信プロセス作成
    send_queue = Queue()
    receive_queue = Queue()
    send_process = Process(target=send, args=(send_queue, send_port))
    receive_process = Process(target=receive, args=(receive_queue, receive_port))
    send_process.start()
    receive_process.start()
    
    time_delay = 0

    input_entered = None
    textbox_width = 300
    textbox_height = 75
    btn_width = 200
    btn_height = 100
    textboxes = [
        TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200,300,75),1),
        TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200+textbox_height*2,300,75),1)]
    btn = Button(u'参戦',
            pygame.Rect(screen_width/2-btn_width/2,screen_width/2-200+textbox_height*3.5,
                btn_width, btn_height))
    
    title_font = pygame.font.Font('ipagp.ttf',70)
    hp_font = pygame.font.Font('ipagp.ttf',30)

    quit = False
    state = 'init'
    #メインループ
    while not quit:
        try:
            time_passed = clock.tick(30)
            passed_seconds = time_passed / 1000.0

            #初期化(一回のみ)
            if state == 'init':
                #オブジェクト・敵データ初期化
                enemy_list = list()
                all_sprites = pygame.sprite.RenderUpdates()
                tanks = pygame.sprite.RenderUpdates()
                Tank.containers = all_sprites, tanks
                walls = pygame.sprite.RenderUpdates()
                Wall.containers = all_sprites, walls
                OuterWall.containers = all_sprites, walls
                adapters = pygame.sprite.RenderUpdates()
                Adapter.containers = all_sprites, adapters
                OuterAdapter.containers = all_sprites, adapters
                bullets = pygame.sprite.RenderUpdates()
                Bullet.containers = all_sprites, bullets
                
                #テキストボックス初期化
                textboxes[0].str_list = list()
                textboxes[1].str_list = list()
                state = 'title'

            #タイトル画面
            elif state == 'title':
                title_surface = title_font.render(u'GunTankOnline',True,(255,255,255))
            
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        for box in textboxes:
                            if box.selected:
                                input_entered = box.char_add(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            for box in textboxes:
                                if box.rect.collidepoint(pygame.mouse.get_pos()):
                                    box.selected = True
                                else:
                                    box.selected = False
                                if btn.rect.collidepoint(pygame.mouse.get_pos()):
                                    id_input = textboxes[0].string
                                    pass_input = textboxes[1].string
                                    if id_input and pass_input:
                                        user_id = id_input
                                        password = pass_input
                                        title_surface = title_font.render(u'待機中です…',True,(255,255,255))
                                        state = 'attend'

                    screen.fill((0,0,0))
                    screen.blit(title_surface,(
                        screen_width/2- title_surface.get_width()/2,
                        screen_height/2 - title_surface.get_height()*2 - 50 ))
                    for box in textboxes:
                        box.update(screen)
                    btn.update(screen)

            #参戦選択後の処理
            elif state == 'attend':
                #自機データ送信,待機ID取得
                try:
                    wait_id = urllib2.urlopen('http://%s/add_wait?id=%s&pass=%s&tank_id=%s&ipaddr=%s'%(server_addr,
                        user_id, password, tank_id, my_ipaddr)).read()
                    int(wait_id)
                #アカウントが不正
                except ValueError:
                    print 'Auth Error'
                    exit()
                else:
                    state = 'wait'
                    
            elif state == 'wait':
                #サーバから承認されて開始データが来るまで待機
                start_data = urllib2.urlopen('http://%s/check_start?wait_id=%s'%(server_addr,wait_id)).read()
                print start_data
                if start_data=='waiting':
                    time.sleep(1)
                else:
                    start_data = json.loads(start_data)
                    #敵データ
                    members = start_data['users'][0]
                    #ステージデータ
                    maze = start_data['users'][1]
                    #各戦車のステータス
                    tank_data = start_data['data']

                    #敵のステータスを初期ステータスから割り付け
                    for tank_num, member in enumerate(members):
                        tank_id_data = tank_data[int(member['tank_id'])]
                        tank_speed = int(tank_id_data['tank_speed'])
                        bullet_speed = int(tank_id_data['bullet_speed'])
                        bullet_per_sec = int(tank_id_data['bullet_per_sec'])
                        hp = int(tank_id_data['hp'])
                        bullet_damage = int(tank_id_data['bullet_damage'])
                        if member['wait_id'] == wait_id:
                            #自機obj生成
                            mytank = Tank(screen_width/2,screen_height/2,'right',
                                        tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage, tank_id, True)
                        else:
                            #敵obj生成
                            enemy_list.append({
                                'obj':Tank(0,0,'right',tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage,tank_id),
                                'ipaddr':member['ip_addr']})

                    make_field(maze, wall_width, wall_height, adapter_width, adapter_height)

                    ipaddr_list = list()
                    for enemy in enemy_list:
                        ipaddr_list.append(enemy['ipaddr'])

                    state = 'play'

            #ゲーム中
            elif state == 'play':
                #受信データを確認
                while not receive_queue.empty():
                    receive_data, ipaddr =  receive_queue.get(block=False)
                    if receive_data['type']=='move':
                        enemy_move(receive_data, ipaddr)
                    elif receive_data['type']=='fire':
                        enemy_fire(receive_data, ipaddr)
                    elif receive_data['type'] == 'struck':
                        enemy_struck(receive_data, ipaddr)

                last_relative_x = mytank.relative_x
                last_relative_y = mytank.relative_y

                tanks.update(mytank.relative_x, mytank.relative_y)
                walls.update(mytank.relative_x, mytank.relative_y)
                adapters.update(mytank.relative_x, mytank.relative_y)
                bullets.update(mytank.relative_x, mytank.relative_y)
                
                #固定obj(壁,アダプタ)との当たり判定
                if pygame.sprite.spritecollideany(mytank, walls) \
                        or pygame.sprite.spritecollideany(mytank, adapters):
                    mytank.relative_x = last_relative_x
                    mytank.relative_y = last_relative_y
                    walls.update(mytank.relative_x, mytank.relative_y)
                    adapters.update(mytank.relative_x, mytank.relative_y)

                #動いた場合に送信
                if last_relative_x != mytank.relative_x or \
                        last_relative_y != mytank.relative_y:
                            send_queue.put({
                                    'ipaddr_list':ipaddr_list,
                                    'type':'move',
                                    'x':mytank.x,
                                    'y':mytank.y,
                                    'way':mytank.way})
                
                screen.fill((255, 255, 255))
                all_sprites.draw(screen)
            
                #ループごとに死亡・全滅確認
                died_list = list()
                for enemy_data in enemy_list:
                    enemy = enemy_data['obj']
                    enemy_hp = enemy.hp
                    if enemy_hp <= 0:
                        enemy_hp = 'DEAD'
                    hp_surface = hp_font.render(str(enemy_hp),True,(0,0,0),(255,255,255))
                    screen.blit(hp_surface,(enemy.rect.x,enemy.rect.y-30))
                    if enemy.hp <= 0:
                        died_list.append(True)
                    else:
                        died_list.append(False)

                if not False in died_list or mytank.hp <= 0:
                    print('died')
                    state = 'init'

                mytank_hp_surface = hp_font.render(str(mytank.hp),True,(0,0,0),(255,255,255))
                screen.blit(mytank_hp_surface,(mytank.rect.x,mytank.rect.y-30))


            pygame.display.update()
            clock.tick(30)
            
        #終了
        except KeyboardInterrupt:
            pygame.quit()
            send_process.terminate()
            receive_process.terminate()
            print('quit')
            exit()