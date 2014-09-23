#coding:utf-8

#NOTICE: REMOVE TEST BEFORE LAUNCH

import pygame
pygame.init()
from pygame.locals import *
import socket
import json
from multiprocessing import Process,Queue
import time
import random
import urllib2
from textbox import TextBox, Button
import pyganim
from math import ceil #切り上げ


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
        #初期HP
        self.default_hp = hp
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

        self.radar = RadarTank(self)

        if self.center:
            #背景を動かすときの相対的な座標
            self.relative_x = -screen_width/2 + wall_height
            self.relative_y = -screen_height/2 + wall_height + wall_width
            self.rect.x = x
            self.rect.y = y

        else:
            #初期化
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
                
            #FOR DEBUG!! TEST
            #強制終了
            elif pressed_keys[K_q]:
                print('SUICIDED')
                self.struck(self.hp)
                
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

            #画面左上の座標
            self.relative_x += x_diff
            self.relative_y += y_diff
            #中心の座標
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
            #他ノードに発射データを送信
            send_queue.put({
                'addresses':addresses,
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
                self.default_x = screen_width/2 + tank.relative_x + tank.height/2
                self.default_y = screen_height/2 + tank.relative_y
            else:
                self.default_x = tank.default_x + tank.width/2
                self.default_y = tank.default_y
            self.image = pygame.transform.rotate(self.origin_image, 90)
        elif tank.way == 'down':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.height/2
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
        #中心に補正
        self.rect.center = (self.default_x, self.default_y)
        self.default_x = self.rect.x
        self.default_y = self.rect.y
        
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
        global struckted_bullet_list
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
            Explode(self.default_x, self.default_y)
        
        #自機に衝突時
        if not self.tank.center and pygame.sprite.collide_rect(self, mytank):
            mytank.struck(self.bullet_damage)
            bullets.remove(self)
            all_sprites.remove(self)
            #x,yは弾が被弾したポイント
            send_queue.put({
                    'addresses':addresses,
                    'type':'struck',
                    'bullet_id':self.bullet_id,
                    'hp':mytank.hp,
                    'x':self.default_x,
                    'y':self.default_y
                    })
            Explode(self.default_x, self.default_y)
            
        #敵が被弾した弾を削除
        for struckted_bullet in struckted_bullet_list:
            if self.bullet_id == struckted_bullet[0]:
                bullets.remove(self)
                all_sprites.remove(self)
                Explode(struckted_bullet[1], struckted_bullet[2])
        struckted_bullet_list = list()

        self.rect.x = self.default_x - relative_x
        self.rect.y = self.default_y - relative_y


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, way):
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.way = way
        self.set_img()

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

    def set_img(self):
        if self.way == 'landscape':
            self.image = wall_landscape
        elif self.way == 'portrait':
            self.image = wall_portrait


class OuterWall(Wall):
    def set_img(self):
        if self.way == 'landscape':
            self.image = outer_wall_landscape
        elif self.way == 'portrait':
            self.image = outer_wall_portrait


class Adapter(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.set_img()

        self.way = 'landscape'
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
        
    def set_img(self):
        self.image = adapter_image


class OuterAdapter(Adapter):
    def set_img(self):
        self.image = outer_adapter_image
        
        
class RadarWall(pygame.sprite.Sprite):
    def __init__(self, x, y, way):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        self.get_img()
        if way == 'landscape':
            self.image = self.wall_landscape
        elif way == 'portrait':
            self.image = self.wall_portrait
        elif way == 'adapter':
            self.image = self.adapter_image
            
        self.rect = self.image.get_rect()
        x += radar_init_x
        y += radar_init_y - radarwall_width #仕様上,下にずれるのの対策
        self.rect.x = x
        self.rect.y = y

    def get_img(self):
        self.wall_landscape = pygame.image.load('./imgs/radarwall.png').convert_alpha()
        self.wall_portrait = pygame.transform.rotate(self.wall_landscape, 90)
        self.adapter_image = pygame.image.load('./imgs/radaradapter.png').convert_alpha()
        
class RadarTank(pygame.sprite.Sprite):
    def __init__(self, tank):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        self.tank = tank
        self.get_img()
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        
    def update(self):
        if self.tank.center:
            x = self.tank.x // 11
            y = self.tank.y // 11
        else:
            x = self.tank.default_x // 11
            y = self.tank.default_y // 11
        x += radar_init_x + radarwall_height
        y += radar_init_y - radarwall_width
        self.rect.x = x
        self.rect.y = y
        
    def get_img(self):
        if self.tank.center:
            self.image = pygame.image.load('./imgs/radarmytank.png').convert_alpha()
        else:
            self.image = pygame.image.load('./imgs/radartank.png').convert_alpha()


#壁,アダプタ(レーダーのも)作成
def make_field(maze, maze_x, maze_y):
    field_x = (wall_width + wall_height) * maze_x - wall_height
    field_y = (wall_width + wall_height) * maze_y - wall_height
    current_y = 0
    maze_lines = maze.split('\n')
    radar_current_y = 0
    for line_num, line in enumerate(maze_lines):
        current_x = 0
        radar_current_x = 0
        line.strip()
        for s_num, s in enumerate(line):
            outer_line = False
            outer_char = False
            if s_num == 0 or s_num == len(line) - 1:
                outer_char = True
            if line_num == len(maze_lines)-2 or line_num == 0:
                outer_line = True

            #文字列パース
            if s == ' ':
                current_x += wall_width
                radar_current_x += radarwall_width
            elif s == '_':
                RadarWall(radar_current_x, radar_current_y + radarwall_width, 'landscape')
                if not(outer_char or outer_line):
                    Wall(current_x, current_y + wall_width, 'landscape')
                else:
                    OuterWall(current_x, current_y + wall_width, 'landscape')
                radar_current_x += radarwall_width
                current_x += wall_width
            elif s == '.':
                RadarWall(radar_current_x, radar_current_y + radarwall_width, 'adapter')
                if not(outer_char or outer_line):
                    Adapter(current_x, current_y + wall_width)
                else:
                    OuterAdapter(current_x, current_y + wall_width)
                radar_current_x += radarwall_height
                current_x += wall_height
            elif s == '|':
                RadarWall(radar_current_x, radar_current_y, 'portrait')
                RadarWall(radar_current_x, radar_current_y + radarwall_width, 'adapter')
                if not outer_char:
                    Wall(current_x, current_y, 'portrait')
                    Adapter(current_x, current_y + wall_width)
                    current_x += wall_height
                else:
                    OuterWall(current_x, current_y, 'portrait')
                    OuterAdapter(current_x, current_y + wall_width)
                    current_x += wall_height
                radar_current_x += radarwall_height

        radar_current_y += radarwall_width
        current_y += wall_width
        
    print('field:',field_x,field_y)
    return current_x, current_y - wall_width

#地面を作成
def make_ground(maze_x, maze_y):
    #inner
    offset_x = wall_height/2
    offset_y = wall_width + wall_height/2
    current_y = offset_y
    for i in range(maze_y):
        current_x = offset_x
        for n in range(maze_x):
            Ground(current_x, current_y)
            current_x += ground_width
        current_y += ground_height
        
    #outer(背景)
    ground_x_num = int(ceil(float(screen_width) / ground_width))
    ground_y_num = int(ceil(float(screen_height) / ground_height))
    current_y = 0
    for i in range(ground_y_num):
        current_x = 0
        for n in range(ground_x_num):
            OuterGround(current_x, current_y)
            current_x += ground_width
        current_y += ground_height

#爆発エフェクト
class Explode(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        self.explode_anim = pyganim.PygAnimation([(img, 0.03) for img in explode_anim_imgs], loop=False)
        self.rect = explode_anim_imgs[0].get_rect()
        
        self.default_x = x
        self.default_y = y
        
        self.explode_anim.play()
        
    def update(self, relative_x, relative_y):
        self.explode_anim.blit(screen, (self.default_x - relative_x - self.rect.width/2,
                                        self.default_y - relative_y - self.rect.height/2))
        if self.explode_anim.isFinished():
            animes.remove(self)
            
#床
class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.set_img()

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

    def set_img(self):
        self.image = ground_image
        
        
class OuterGround(Ground):
    def update(self):
        pass
    
    def set_img(self):
        self.image = outer_ground_image

#
#転送周り
def send(send_queue):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            while not send_queue.empty():
                send_data = send_queue.get(block=False)
                for address in send_data['addresses']:
                    sock.sendto(json.dumps(send_data), (address[0], address[1]))
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
    struckted_bullet_list.append((receive_data['bullet_id'],
                                  receive_data['x'],
                                  receive_data['y']))

#初期位置の候補をランダムに
def init_place(field_x, field_y, wall_width):
    print("field:{},{}".format(field_x, field_y))
    start_x = random.randint(wall_width, field_x - wall_width)
    start_y = random.randint(wall_width, field_y - wall_width)
    
    return start_x, start_y

#正確な現在時刻
def nowtime():
    return time.time() + time_offset

if __name__ == '__main__':
    #proxy対策
    my_ipaddr = raw_input('MyIPaddr> ')

    #debug
    if my_ipaddr=='localhost':
        debug = True
        my_ipaddr = '127.0.0.1'
        server_addr = '127.0.0.1:5000'
        receive_port = int(raw_input('RECV PORT> '))
    else:
        server_addr = raw_input('ServerAddr> ')
        debug = False
        receive_port = 8800
    
    screen_width = 1024
    screen_height = 768
    #tank_idに対応したファイル名
    tank_id_file = ('./imgs/0_tank.png','./imgs/1_tank.png','./imgs/2_tank.png','./imgs/3_tank.png')
    bullet_id_file = ('./imgs/0_bullet.png','./imgs/1_bullet.png',
                      './imgs/2_bullet.png','./imgs/3_bullet.png')
    
    #フィールドサイズ
    maze_x = 10
    maze_y = 10
    
    screen = pygame.display.set_mode([screen_width, screen_height])

    pygame.display.set_caption('GTO -Gun Tank Online-')
    clock = pygame.time.Clock()
    
    #時刻の差を取得
    time_offset = float(urllib2.urlopen('http://{}/time'.format(server_addr)).read()) - time.time()

    #各パーツの寸法をチェック
    check_img = pygame.image.load('./imgs/wall.png')
    wall_width = check_img.get_width()
    wall_height = check_img.get_height()
    
    check_img = pygame.image.load('./imgs/adapter.png')
    adapter_width = check_img.get_width()
    adapter_height = check_img.get_height()
    
    check_img = pygame.image.load('./imgs/radarwall.png')
    radarwall_width = check_img.get_width()
    radarwall_height = check_img.get_height()
    
    check_img = pygame.image.load('./imgs/ground.png')
    ground_width = check_img.get_width()
    ground_height = check_img.get_height()
    
    #レーダー背景
    radar_img = pygame.image.load('./imgs/radar.png').convert_alpha()
    #レーダー表示位置
    radar_init_x = screen_width - 350
    radar_init_y = 30
    
    #HPバー
    hp_green_img = pygame.image.load('./imgs/hp_green.png').convert_alpha()
    hp_red_img = pygame.image.load('./imgs/hp_red.png').convert_alpha()
    hpback_img = pygame.image.load('./imgs/hpback.png').convert_alpha()
    #HP/名前の背景
    statusback_img = pygame.image.load('./imgs/statusback.png').convert_alpha()
    #自機ステータス
    mystatusback_img = pygame.image.load('./imgs/mystatusback.png').convert()
    mystatus_x = screen_width - 410
    mystatus_y = screen_height - 150
    myhp_green_img = pygame.image.load('./imgs/myhp_green.png').convert()
    myhp_red_img = pygame.image.load('./imgs/myhp_red.png').convert()
    myhpbarback_img = pygame.image.load('./imgs/myhpback.png').convert()
    
    #爆発アニメ
    explode_anim_imgs = [pygame.image.load('./imgs/explode/{}.png'.format(n)).convert_alpha() for n in range(15)]

    #TODO グラフィック番号変更可能に
    #戦車のグラフィック番号
    tank_id = 0
    
    #送受信データキュー,送受信プロセス作成
    send_queue = Queue()
    receive_queue = Queue()
    send_process = Process(target=send, args=(send_queue,))
    receive_process = Process(target=receive, args=(receive_queue, receive_port))
    send_process.start()
    receive_process.start()
    
    #テキストボックス
    #input_entered = None
    #textbox_width = 300
    #textbox_height = 75
    #btn_width = 200
    #btn_height = 100
    #textboxes = [
        #TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200,300,75),1),
        #TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200+textbox_height*2,300,75),1)]
    #btn = Button(u'参戦',
            #pygame.Rect(screen_width/2-btn_width/2,screen_width/2-200+textbox_height*3.5,
                #btn_width, btn_height))
    
    title_font = pygame.font.Font('ipagp.ttf',70)
    tankname_font = pygame.font.Font('ipagp.ttf', 20)
    mystatus_font = pygame.font.Font('ipagp.ttf', 30)
    myhp_descript =  mystatus_font.render('HP', True, (255,255,255))
    myshot_descript =  mystatus_font.render('Shot', True, (255,255,255))
    mybomb_descript =  mystatus_font.render('Bomb', True, (255,255,255))

    quit = False
    state = 'init'
    #メインループ
    while not quit:
        try:
            time_passed = clock.tick(30)
            passed_seconds = time_passed / 1000.0

            #初期化
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
                radarwalls = pygame.sprite.RenderUpdates()
                RadarWall.containers = all_sprites, radarwalls
                radartanks = pygame.sprite.RenderUpdates()
                RadarTank.containers = all_sprites, radartanks
                animes = pygame.sprite.RenderUpdates()
                Explode.containers = animes
                grounds = pygame.sprite.RenderUpdates()
                Ground.containers = grounds
                outergrounds = pygame.sprite.RenderUpdates()
                OuterGround.containers = outergrounds
                
                #敵が被弾した弾リスト初期化
                struckted_bullet_list = list()
                
                #テキストボックス初期化
                #if debug:
                    #textboxes[0].str_list = list(str(user_id))
                    #textboxes[1].str_list = list(str(password))
                #else:
                    #textboxes[0].str_list = list()
                    #textboxes[1].str_list = list()
                state = 'attend'

            #タイトル画面
            #elif state == 'title':
                #title_surface = title_font.render(u'GunTankOnline',True,(255,255,255))
            
                #for event in pygame.event.get():
                    #if event.type == pygame.KEYDOWN:
                        #for box in textboxes:
                            #if box.selected:
                                #input_entered = box.char_add(event)
                    #elif event.type == pygame.MOUSEBUTTONDOWN:
                        #if event.button == 1:
                            #for box in textboxes:
                                #if box.rect.collidepoint(pygame.mouse.get_pos()):
                                    #box.selected = True
                                #else:
                                    #box.selected = False
                                #if btn.rect.collidepoint(pygame.mouse.get_pos()):
                                    #id_input = textboxes[0].string
                                    #pass_input = textboxes[1].string
                                    #if id_input and pass_input:
                                        #user_id = id_input
                                        #password = pass_input
                                        #title_surface = title_font.render(u'待機中です…',True,(255,255,255))
                                        #state = 'attend'

                    #screen.fill((0,0,0))
                    #screen.blit(title_surface,(
                        #screen_width/2- title_surface.get_width()/2,
                        #screen_height/2 - title_surface.get_height()*2 - 50 ))
                    #for box in textboxes:
                        #box.update(screen)
                    #btn.update(screen)

            #参戦選択後の処理
            elif state == 'attend':
                #自機データ送信,セッションID取得
                data = {'ipaddr':my_ipaddr, 'port':receive_port, 'tank_id':tank_id}
                mysession_id = int(json.loads(urllib2.urlopen('http://{}/attend?json={}'.format(server_addr,
                                              urllib2.quote(json.dumps(data)))).read())['session_id'])
                state = 'wait'
                    
            elif state == 'wait':
                #サーバから承認されて開始データが来るまで待機
                data = json.loads(urllib2.urlopen('http://{}/check'.format(server_addr)).read())
                if not data['start']:
                    print('...')
                else:
                    print('{} people are waiting...'.format(data['waiting']))
                    start_time = data['start_time']
                    battle_id = data['battle_id']
                    if start_time < nowtime():
                        state = 'start'
                if not state=='start':
                    time.sleep(0.5)
                    
            elif state == 'start':
                data = json.loads(urllib2.urlopen('http://{}/start?battle_id={}'.format(server_addr, battle_id)).read())
                maze = data[0]
                players = data[1]
                tank_dataset = data[2]

                #敵のステータスを初期ステータスから割り付け
                for player in players:
                    tankdata = tank_dataset[int(player['tank_id'])]
                    session_id = int(player['session_id'])
                    tank_speed = int(tankdata['tank_speed'])
                    bullet_speed = int(tankdata['bullet_speed'])
                    bullet_per_sec = int(tankdata['bullet_per_sec'])
                    hp = int(tankdata['hp'])
                    bullet_damage = int(tankdata['bullet_damage'])
                    accel_ratio = float(tankdata['accel_ratio'])
                    brake_ratio = float(tankdata['brake_ratio'])
                    
                    if session_id == mysession_id:
                        print('build mine')
                        #自機obj生成
                        mytank = Tank(screen_width/2,screen_height/2,'right',
                                    tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage, tank_id, True,
                                    accel_ratio, brake_ratio)
                    else:
                        #敵obj生成
                        print('build enemy')
                        enemy_list.append({
                            'obj':Tank(0,0,'right',tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage,tank_id),
                            'ipaddr':player['ipaddr'],
                            'port':player['port']})

                #画像準備
                wall_landscape = pygame.image.load('./imgs/wall.png').convert()
                wall_portrait = pygame.transform.rotate(wall_landscape, 90)
                outer_wall_landscape = pygame.image.load('./imgs/outer_wall.png').convert()
                outer_wall_portrait = pygame.transform.rotate(outer_wall_landscape, 90)
                adapter_image = pygame.image.load('./imgs/adapter.png').convert()
                outer_adapter_image = pygame.image.load('./imgs/outer_adapter.png').convert()
                ground_image = pygame.image.load('./imgs/ground.png').convert()
                outer_ground_image = pygame.image.load('./imgs/outer_ground.png').convert()

                field_x, field_y = make_field(maze, maze_x, maze_y)
                make_ground(maze_x, maze_y)

                #アドレスリスト作成
                addresses = list()
                for enemy in enemy_list:
                    addresses.append([enemy['ipaddr'],enemy['port']])

                #初期位置設定
                while True:
                    #ランダムな位置をゲット
                    start_x, start_y = init_place(field_y, field_y, wall_width)
                    start_x -= screen_width/2
                    start_y -= screen_height/2
                    print("try:{},{}".format(start_x,start_y))
                    #start_x,yを反映
                    mytank.relative_x = start_x
                    mytank.relative_y = start_y
                    tanks.update(mytank.relative_x, mytank.relative_y)
                    walls.update(mytank.relative_x, mytank.relative_y)
                    adapters.update(mytank.relative_x, mytank.relative_y)
                    #接触していない場合はループから離脱
                    if not (pygame.sprite.spritecollideany(mytank, walls) \
                        or pygame.sprite.spritecollideany(mytank, adapters)):
                        break
                    
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
                grounds.update(mytank.relative_x, mytank.relative_y)
                outergrounds.update()
                
                #固定obj(壁,アダプタ),他の機体と機体との当たり判定
                if pygame.sprite.spritecollideany(mytank, walls) \
                        or pygame.sprite.spritecollideany(mytank, adapters):
                        #or len(pygame.sprite.spritecollide(mytank, tanks, False))>1:
                    #最後のは他の機体
                    #プラス方向に移動した場合
                    if last_relative_x < mytank.relative_x:
                        mytank.relative_x -= 2*(mytank.relative_x - last_relative_x)
                    elif last_relative_x > mytank.relative_x:
                        mytank.relative_x += 2*(last_relative_x - mytank.relative_x)
                    
                    if last_relative_y < mytank.relative_y:
                        mytank.relative_y -= 2*(mytank.relative_y - last_relative_y)
                    elif last_relative_y > mytank.relative_y:
                        mytank.relative_y += 2*(last_relative_y - mytank.relative_y)
                   
                    walls.update(mytank.relative_x, mytank.relative_y)
                    adapters.update(mytank.relative_x, mytank.relative_y)
                    tanks.update(mytank.relative_x, mytank.relative_y)

                #機体が動いた場合に送信
                if last_relative_x != mytank.relative_x or \
                        last_relative_y != mytank.relative_y:
                            send_queue.put({
                                'addresses':addresses,
                                'type':'move',
                                'x':mytank.x,
                                'y':mytank.y,
                                'way':mytank.way})
                
                #レーダーの機体を更新
                radartanks.update()
                
                #描画
                screen.fill((187, 127, 90))
                outergrounds.draw(screen)
                grounds.draw(screen)
                bullets.draw(screen)
                tanks.draw(screen)
                walls.draw(screen)
                adapters.draw(screen)
                
                #アニメーションを更新
                animes.update(mytank.relative_x, mytank.relative_y)
                
                #自機死亡・全滅確認
                died_list = list()
                for enemy_data in enemy_list:
                    #TODO tankname 動的取得
                    tankname = 'NAME1'
                    
                    enemy = enemy_data['obj']
                    
                    #HP/ネーム背景
                    status_x = enemy.rect.x - 30
                    status_y = enemy.rect.y - 55
                    screen.blit(statusback_img, (status_x, status_y))
                    
                    #ユーザー名描画
                    tankname_surface = tankname_font.render(tankname, True, (255, 255, 255))
                    screen.blit(tankname_surface, (status_x + 10, status_y + 5))
                    
                    #HPバー背景(削れたぶん)
                    screen.blit(hpback_img, (status_x + 10, status_y + 30))
                    
                    #HPバー
                    hp_percent = (float(enemy.hp) / enemy.default_hp)*100
                    if hp_percent > 40:
                        hpbar_img = hp_green_img
                    else:
                        hpbar_img = hp_red_img
                    hpbar_length = int((hp_percent/100) * hp_green_img.get_width())
                    screen.blit(hpbar_img, (status_x + 10, status_y + 30),
                                area=pygame.Rect(0, 0, hpbar_length, hp_green_img.get_height()))
                    
                    if enemy.hp <= 0:
                        died_list.append(True)
                    else:
                        died_list.append(False)

                if not False in died_list or mytank.hp <= 0:
                    print('died')
                    state = 'init'
                    
                #レーダー描画
                screen.blit(radar_img, (radar_init_x, radar_init_y)) #レーダー画面
                radartanks.draw(screen)
                radarwalls.draw(screen)
                
                #自機ステータス表示
                screen.blit(mystatusback_img, (mystatus_x, mystatus_y))
                #自機HP
                screen.blit(myhp_descript, (mystatus_x + 5, mystatus_y + 5))
                screen.blit(myhpbarback_img, (mystatus_x + 105, mystatus_y + 5))
                myhp_percent = (float(mytank.hp) / mytank.default_hp)*100
                if myhp_percent > 40:
                    myhpbar_img = myhp_green_img
                else:
                    myhpbar_img = myhp_red_img
                myhpbar_length = int((myhp_percent/100) * myhp_green_img.get_width())
                screen.blit(myhpbar_img, (mystatus_x + 105, mystatus_y + 5),
                            area=pygame.Rect(0, 0, myhpbar_length, myhp_green_img.get_height()))
                            
                #ショットたまり具合
                screen.blit(myshot_descript, (mystatus_x + 5, mystatus_y + 40))
                
                #ボム数
                screen.blit(mybomb_descript, (mystatus_x + 5, mystatus_y + 75))
                
            pygame.display.update()
            clock.tick(30)
            
        #終了
        except KeyboardInterrupt:
            pygame.quit()
            send_process.terminate()
            receive_process.terminate()
            print('quit')
            exit()