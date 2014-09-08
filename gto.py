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
            hp, bullet_damage, tank_id, center=None, accel_ratio=None, brake_ratio=None):
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
        
        #各方向の速度
        self.x_speed = 0
        self.y_speed = 0
        self.accel_ratio = accel_ratio
        self.brake_ratio = brake_ratio

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
        
            brake_ratio = self.brake_ratio
            accel_ratio = self.accel_ratio
        
            #前フレームからのdiff
            x_diff = 0
            y_diff = 0

            #移動
            pygame.event.pump()
            pressed_keys = pygame.key.get_pressed()
            last_way = self.way
            if pressed_keys[K_UP] or pressed_keys[K_w]:
                self.way = 'up'
                #反対に動いている場合
                if self.y_speed > 0:
                    self.y_speed -= 2 * accel_ratio * passed_seconds
                else:
                    self.y_speed -= accel_ratio * passed_seconds
                #制限速度管理
                if self.y_speed < -self.speed: self.y_speed = -self.speed
                #何もないなら自動で減速
                self.x_speed = int(self.x_speed * brake_ratio * 0.5)
                    
            elif pressed_keys[K_DOWN] or pressed_keys[K_s]:
                self.way = 'down'
                if self.y_speed < 0:
                    self.y_speed += 2 * accel_ratio * passed_seconds
                else:
                    self.y_speed += accel_ratio * passed_seconds
                if self.y_speed > self.speed: self.y_speed = self.speed
                self.x_speed = int(self.x_speed * brake_ratio * 0.5)
                
            elif pressed_keys[K_LEFT] or pressed_keys[K_a]:
                self.way = 'left'
                if self.x_speed > 0:
                    self.x_speed -= 2 * accel_ratio * passed_seconds
                else:
                    self.x_speed -= accel_ratio * passed_seconds
                if self.x_speed < -self.speed: self.x_speed = -self.speed
                self.y_speed = int(self.y_speed * brake_ratio * 0.5)                    
                
            elif pressed_keys[K_RIGHT] or pressed_keys[K_d]:
                self.way = 'right'
                if self.x_speed < 0:
                    self.x_speed += 2 * accel_ratio * passed_seconds
                else:
                    self.x_speed += accel_ratio * passed_seconds
                if self.x_speed > self.speed: self.x_speed = self.speed
                self.y_speed = int(self.y_speed * brake_ratio * 0.5)                
                
            else:
                self.x_speed = int(self.x_speed * brake_ratio)
                self.y_speed = int(self.y_speed * brake_ratio)
                
                #小さい時は0にしてしまう
                if abs(self.x_speed) < 5:
                    self.x_speed = 0
                if abs(self.y_speed) < 5:
                    self.y_speed = 0

            x_diff = self.x_speed * passed_seconds
            y_diff = self.y_speed * passed_seconds
        
            print((self.x_speed, self.y_speed))

            #方向固定
            if pressed_keys[K_z]:
                self.way = last_way
                if self.way == 'up' or self.way == 'down':
                    x_diff = 0
                elif self.way == 'left' or self.way == 'right':
                    y_diff = 0

            #発射
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

    def fire(self, speed, bullet_id=None, colid_point=None):
        if self.center:
            bullet_id = random.randint(1, 99999999)
            bullet = Bullet(self, speed, bullet_id, self.bullet_damage)
            send_queue.put({
                'ipaddr_list':ipaddr_list,
                'type':'fire',
                'time':time.time(),
                'x':self.x,
                'y':self.y,
                'way':self.way,
                'bullet_id':bullet_id,
                'speed':speed,
                'colid_point':bullet.colid_point,
                })
        else:
            Bullet(self, speed,bullet_id, self.bullet_damage, colid_point)

    def struck(self, bullet_damage):
        self.hp -= bullet_damage


class Bullet(pygame.sprite.Sprite):
    def __init__(self, tank, speed, bullet_id, bullet_damage, colid_point=None):
        self.tank = tank
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.clock = pygame.time.Clock()
        self.clock.tick()

        self.bullet_id = bullet_id
        self.bullet_damage = bullet_damage

        self.origin_image = pygame.image.load(bullet_id_file[self.tank.tank_id]).convert_alpha()

        #発射される初期位置を設定
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
            
            #壁との衝突予定ポイントを計算
            #衝突を検知するrectの大きさ
            max_detect = 5000
            if tank.way == 'up' or tank.way == 'down':
                detect_rect = self.rect.inflate(0, max_detect)
            else:
                detect_rect = self.rect.inflate(max_detect, 0)
                
            #弾の飛んでいく方向にdetect_rectの位置を合わせる
            if tank.way == 'up':
                detect_rect.y = self.rect.y - max_detect
            elif tank.way == 'down':
                detect_rect.y = self.rect.y
            elif tank.way == 'left':
                detect_rect.x = self.rect.x - max_detect
            elif tank.way == 'right':
                detect_rect.x = self.rect.x
            detect_sprite = pygame.sprite.Sprite()
            detect_sprite.rect = detect_rect
            #衝突予定rect
            strike_sprites = pygame.sprite.spritecollide(detect_sprite, walls, False)
            #衝突する可能性のあるxまたはy座標のリスト
            colid_points = list()
            for strike_sprite in strike_sprites:
                if tank.way == 'left' or tank.way == 'right':
                    if strike_sprite.way == 'portrait':
                        colid_points.append(strike_sprite.default_x)
                    elif strike_sprite.way == 'landscape':
                        colid_points.append(strike_sprite.default_x + strike_sprite.width)
                elif tank.way == 'up' or tank.way == 'down':
                    if strike_sprite.way == 'landscape':
                        colid_points.append(strike_sprite.default_y)
                    elif strike_sprite.way == 'portrait':
                        colid_points.append(strike_sprite.default_y + strike_sprite.width)

            if self.way == 'down' or self.way == 'right':
                colid_point = min(colid_points)
            else:
                colid_point = max(colid_points)
                
        else:
            self.rect.x = self.default_x - mytank.relative_x
            self.rect.y = self.default_y - mytank.relative_y
            
        #衝突予定座標
        self.colid_point = colid_point

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
        if self.way == 'left' and self.default_x<=self.colid_point \
            or self.way == 'right' and self.default_x>=self.colid_point \
                or self.way == 'up' and self.default_y<=self.colid_point \
                    or self.way == 'down' and self.default_y>=self.colid_point:
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
        self.way = way

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

        self.way = 'landscape'
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
            enemy['obj'].fire(receive_data['speed'],receive_data['bullet_id'],
                              receive_data['colid_point'])

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

    #debug
    if my_ipaddr=='localhost':
        debug = True
        my_ipaddr = '127.0.0.1'
        server_addr = '127.0.0.1:5000'
        send_port = int(raw_input('SEND PORT> '))
        receive_port = int(raw_input('RECV PORT> '))
        #クライアント0か1か確認
        client_num = int(raw_input('Client 0/1? > '))
        #ユーザを固定しておく
        if client_num:
            user_id = 19623
            password = 77681
        else:
            user_id = 41170
            password = 84981
    else:
        debug = False
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
    
    #削除する弾リスト
    struckted_bullet_list = list()
    
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
                start_x = int(raw_input('START X> '))
                start_y = int(raw_input('Y> '))
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
                if debug:
                    textboxes[0].str_list = list(str(user_id))
                    textboxes[1].str_list = list(str(password))
                else:
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
                start_data = json.loads(start_data)
                if start_data['state']=='wait':
                    print('... ',)
                    time.sleep(1)
                elif start_data['state']=='start':
                    #敵データ
                    members = start_data['users']
                    #ステージデータ
                    maze = start_data['maze']
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
                        accel_ratio = float(tank_id_data['accel_ratio'])
                        brake_ratio = float(tank_id_data['brake_ratio'])
                        
                        if member['wait_id'] == wait_id:
                            #自機obj生成
                            mytank = Tank(screen_width/2,screen_height/2,'right',
                                        tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage, tank_id, True,
                                        accel_ratio, brake_ratio)
                        else:
                            #敵obj生成
                            enemy_list.append({
                                'obj':Tank(0,0,'right',tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage,tank_id),
                                'ipaddr':member['ip_addr']})

                    make_field(maze, wall_width, wall_height, adapter_width, adapter_height)

                    ipaddr_list = list()
                    for enemy in enemy_list:
                        ipaddr_list.append(enemy['ipaddr'])
                        
                    #remove
                    #
                    mytank.relative_x = start_x
                    mytank.relative_y = start_y

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

                #移動前の位置を格納
                last_relative_x = mytank.relative_x
                last_relative_y = mytank.relative_y

                #各オブジェクトをupdate
                tanks.update(mytank.relative_x, mytank.relative_y)
                walls.update(mytank.relative_x, mytank.relative_y)
                adapters.update(mytank.relative_x, mytank.relative_y)
                bullets.update(mytank.relative_x, mytank.relative_y)
                
                #固定obj(壁,アダプタ)と機体との当たり判定
                if pygame.sprite.spritecollideany(mytank, walls) \
                        or pygame.sprite.spritecollideany(mytank, adapters) \
                        or len(pygame.sprite.spritecollide(mytank, tanks, False))>1:
                    mytank.relative_x = last_relative_x
                    mytank.relative_y = last_relative_y
                    walls.update(mytank.relative_x, mytank.relative_y)
                    adapters.update(mytank.relative_x, mytank.relative_y)
                    tanks.update(mytank.relative_x, mytank.relative_y)

                #機体が動いた場合に送信
                if last_relative_x != mytank.relative_x or \
                        last_relative_y != mytank.relative_y:
                            send_queue.put({
                                    'ipaddr_list':ipaddr_list,
                                    'type':'move',
                                    'x':mytank.x,
                                    'y':mytank.y,
                                    'way':mytank.way})
                
                screen.fill((187, 127, 90))
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