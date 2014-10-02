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
        self.bomb_per_sec = 0.2
        self.bomb_wait_sec = 1 / self.bomb_per_sec
        self.bomb_passed_sec = self.bomb_wait_sec

        self.radar = RadarTank(self)
        
        #死亡
        self.died = False

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

    def update(self, relative_x, relative_y, countdown):
        #今死んだ場合
        if not self.died and self.hp <= 0:
            self.deadtime = nowtime()
        self.died = self.hp <= 0
        if self.center:
            passed_seconds = self.clock.tick()/1000.0
        
            brake_ratio = self.brake_ratio
            accel_ratio = self.accel_ratio
        
            #前フレームからのdiff
            x_diff = 0
            y_diff = 0
            
            pygame.event.pump()
            #カウントダウン中動きをキャンセル
            if not block:
                #移動
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
                    send_queue.put({
                    'addresses':addresses,
                    'session_id':mysession_id,
                    'type':'struck',
                    'bullet_id':0,
                    'hp':self.hp,
                    'x':self.x,
                    'y':self.y,
                    'died':self.died
                    })
                    
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
                self.bullet_passed_sec += passed_seconds #発射間隔を満たしている場合
                if pressed_keys[K_SPACE] and \
                        self.bullet_passed_sec * self.bullet_per_sec >= 1:
                    if x_diff or y_diff:
                        self.fire(self.speed + self.bullet_speed)
                    else:
                        self.fire(self.bullet_speed)
                    self.bullet_passed_sec = 0
                
                #ボム
                self.bomb_passed_sec += passed_seconds
                if pressed_keys[K_x] and \
                        self.bomb_passed_sec >= self.bomb_wait_sec:
                    self.bombed()
                    self.bomb_passed_sec = 0
            
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
        global fired_bullet_list
        if self.center:
            bullet_id = random.randint(1, 99999999)
            bullet = Bullet(self, speed, bullet_id, self.bullet_damage)
            #他ノードに発射データを送信
            send_queue.put({
                'addresses':addresses,
                'session_id':mysession_id,
                'type':'fire',
                'x':self.x,
                'y':self.y,
                'way':self.way,
                'bullet_id':bullet_id,
                'speed':speed,
                'colid_point':bullet.colid_point,
                })
            #自分が打った弾リスト
            fired_bullet_list.append(bullet_id)
        else:
            Bullet(self, speed,bullet_id, self.bullet_damage, colid_point)
           
        

    def struck(self, bullet_damage=None):
        if self.center:
            self.hp -= bullet_damage
        #死亡時のグラ入れ替え
        if self.died:
            self.origin_image = pygame.image.load(diedtank_id_file[tank_id]).convert_alpha()
            if self.way == 'up':
                self.up_image = pygame.transform.rotate(self.origin_image, 270)
                self.image = self.up_image
            elif self.way == 'down':
                self.down_image = pygame.transform.rotate(self.origin_image, 90)
                self.image = self.down_image
            elif self.way == 'left':
                self.image = self.origin_image
            elif self.way == 'right':
                self.right_image = pygame.transform.rotate(self.origin_image, 180)
                self.image = self.right_image
                
    def bombed(self, explode_time=None, bullet_id=None):
        if self.center:
            #爆発を3s後に設定
            bullet_id = random.randint(1, 99999999)
            explode_time = nowtime() + 3
            
            send_queue.put({
                'addresses':addresses,
                'session_id':mysession_id,
                'type':'bomb',
                'bullet_id':bullet_id,
                'x':self.x,
                'y':self.y,
                'explode':explode_time
                })
            
            Bomb(self, self.x, self.y, explode_time, bullet_id)
            bombed_list.append(bullet_id)
        else:
            Bomb(self, self.default_x, self.default_y, explode_time, bullet_id)


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
        Explode(self.default_x, self.default_y, 'small')
        #中心に補正
        self.rect.center = (self.default_x, self.default_y)
        self.default_x = self.rect.x
        self.default_y = self.rect.y
        
        self.way = tank.way
        self.speed = speed
        
        #弾の当たり判定部分を拡大して,弾が透けるのを軽減
        if self.way == 'up' or self.way == 'down':
            self.rect.inflate_ip(0,50)
        else:
            self.rect.inflate_ip(50,0)
        
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

            try:
                if self.way == 'down' or self.way == 'right':
                    colid_point = min(colid_points)
                else:
                    colid_point = max(colid_points)
            except ValueError:
                colid_point = (0, 0)
                
        else:
            self.rect.x = self.default_x - mytank.relative_x
            self.rect.y = self.default_y - mytank.relative_y
            
        #衝突予定座標
        self.colid_point = colid_point
        
    def update(self, relative_x, relative_y):
        global struckted_bullet_list
        global fired_bullet_list
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
            #自分が発射した弾丸なら発射済みリストから削除
            try:
                fired_bullet_list.remove(self.bullet_id)
            except ValueError:
                pass
        
        #自機に衝突時
        if not self.tank.center and pygame.sprite.collide_rect(self, mytank)\
            and not self.bullet_id in fired_bullet_list:
            mytank.struck(self.bullet_damage)
            bullets.remove(self)
            all_sprites.remove(self)
            #x,yは弾が被弾したポイント
            send_queue.put({
                    'addresses':addresses,
                    'session_id':mysession_id,
                    'type':'struck',
                    'bullet_id':self.bullet_id,
                    'hp':mytank.hp,
                    'x':self.default_x,
                    'y':self.default_y,
                    'died':self.tank.died
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
        
        
class Bomb(pygame.sprite.Sprite):
    def __init__(self, tank, x, y, explode_time, bullet_id):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        self.tank = tank
        self.explode_time = explode_time
        self.default_x = x
        self.default_y = y
        self.bullet_id = bullet_id
        self.bomb_anim = pyganim.PygAnimation([(img, 0.3) for img in bombanim_imgs], loop=True)
        self.rect = bombanim_imgs[0].get_rect()
        self.bomb_anim.play()
        self.state = 'wait'
        
    def update(self, relative_x, relative_y):
        exploding = nowtime() > self.explode_time
        
        if not exploding:
            self.bomb_anim.blit(screen, (self.default_x - relative_x - self.rect.width/2,
                                        self.default_y - relative_y - self.rect.height/2))
        #爆発開始時
        elif exploding and self.state == 'wait':
            self.explode = Explode(self.default_x, self.default_y, 'bomb')
            detect_sprite = pygame.sprite.Sprite()
            detect_sprite.rect = self.explode.explode_anim.getFrame(0).get_rect()
            detect_sprite.rect.center = (self.default_x - relative_x, self.default_y - relative_y)
            #壁破壊
            damage_walls = pygame.sprite.spritecollide(detect_sprite, walls, False, pygame.sprite.collide_circle)
            for damage_wall in damage_walls:
                #Outerでないとき
                if damage_wall.__class__.__name__ == 'Wall':
                    DamagedWall((damage_wall.default_x, damage_wall.default_y),
                                damage_wall.way, damage_wall.radar)
                    walls.remove(damage_wall)
                    all_sprites.remove(damage_wall)
            
            #自機に当たったかどうか
            damaged = pygame.sprite.collide_rect(mytank, detect_sprite)
            if damaged:
                damage_hp = 100
                mytank.struck(damage_hp)
                send_queue.put({
                    'addresses':addresses,
                    'session_id':mysession_id,
                    'type':'struck',
                    'bullet_id':self.bullet_id,
                    'hp':mytank.hp,
                    'x':mytank.x,
                    'y':mytank.y,
                    'died':mytank.died
                })
                Explode(mytank.x, mytank.y)
                
            self.state = 'exploded'
            
        elif self.explode.explode_anim.isFinished():
            Crater(self.default_x, self.default_y)
            bombs.remove(self)
            all_sprites.remove(self)
            
            
class Crater(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.default_x = x
        self.default_y = y
        
        self.image = pygame.image.load('imgs/crater.png').convert_alpha()
        self.rect = self.image.get_rect()
    
    def update(self, relative_x, relative_y):
        self.rect.center = (self.default_x-relative_x,self.default_y-relative_y)


class Wall(pygame.sprite.Sprite):
    def __init__(self, position, radarposition, way):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        x, y = position
        self.radar = RadarWall(radarposition, way)

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
        elif self.way == 'adapter':
            self.image = adapter_image


class OuterWall(Wall):
    def set_img(self):
        if self.way == 'landscape':
            self.image = outer_wall_landscape
        elif self.way == 'portrait':
            self.image = outer_wall_portrait
        elif self.way == 'adapter':
            self.image = outer_adapter_image
            

class DamagedWall(pygame.sprite.Sprite):
    def __init__(self, position, way, radar):
        pygame.sprite.Sprite.__init__(self, self.containers)

        x, y  = position
        self.radar = radar
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
            self.image = damagedwall_landscape
            self.radar.image = self.radar.damagedwall_landscape
        elif self.way == 'portrait':
            self.image = damagedwall_portrait
            self.radar.image = self.radar.damagedwall_portrait
        elif self.way == 'adapter':
            self.image = damagedadapter_image
            self.radar.image = self.radar.damagedadapter_image
        
        
class RadarWall(pygame.sprite.Sprite):
    def __init__(self, position, way):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        x, y = position
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
        self.damagedwall_landscape = pygame.image.load('./imgs/damagedradarwall.png').convert_alpha()
        self.wall_portrait = pygame.transform.rotate(self.wall_landscape, 90)
        self.damagedwall_portrait = pygame.transform.rotate(self.damagedwall_landscape, 90)
        self.adapter_image = pygame.image.load('./imgs/radaradapter.png').convert_alpha()
        self.damagedadapter_image = pygame.image.load('./imgs/damagedradaradapter.png').convert_alpha()
        
        
class RadarTank(pygame.sprite.Sprite):
    def __init__(self, tank):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        self.tank = tank
        self.get_img()
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        
    def update(self):
        #死亡時グラ入れ替え
        if self.tank.died:
            self.image = self.diedimage
        
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
            self.diedimage = self.image
        else:
            self.image = pygame.image.load('./imgs/radartank.png').convert_alpha()
            self.diedimage = pygame.image.load('./imgs/diedradartank.png').convert_alpha()
            
            
#爆発エフェクト
class Explode(pygame.sprite.Sprite):
    def __init__(self, x, y, size='big'):
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        if size == 'small':
            anim_imgs = smallexplode_anim_imgs
            self.explode_anim = pyganim.PygAnimation([(img, 0.03) for img in anim_imgs], loop=False)
        elif size=='big':
            anim_imgs = explode_anim_imgs
            self.explode_anim = pyganim.PygAnimation([(img, 0.03) for img in anim_imgs], loop=False)
        elif size == 'bomb':
            anim_imgs = bombexplodeanim_imgs
            self.explode_anim = pyganim.PygAnimation([(img, 0.03) for img in anim_imgs], loop=False)
            
        self.image = anim_imgs[0]
        self.rect = anim_imgs[0].get_rect()
        
        self.default_x = x
        self.default_y = y
        
        self.explode_anim.play()
        
    def update(self, relative_x, relative_y):
        self.explode_anim.blit(screen, (self.default_x - relative_x - self.rect.width/2,
                                        self.default_y - relative_y - self.rect.height/2))
        if self.explode_anim.isFinished():
            bombs.remove(self)
            
            
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


#壁,アダプタ(レーダーのも)作成
def make_field(maze, maze_x, maze_y):
    field_x = (wall_width + wall_height) * maze_x - wall_height
    field_y = (wall_width + wall_height) * maze_y - wall_height
    current_y = 0
    maze_lines = maze.split('\n')
    radar_current_y = 0
    #1つ前の文字が' 'ならスペースの幅を壁と同じに
    last_char = None
    for line_num, line in enumerate(maze_lines):
        current_x = 0
        radar_current_x = 0
        line.strip()
        for s_num, s in enumerate(line):
            outer_line = False
            outer_char = False
            if s_num == 0 or s_num == len(line) - 1:
                outer_char = True
            if line_num == len(maze_lines)-1 or line_num == 0:
                outer_line = True

            #文字列パース
            if s == ' ':
                if last_char == ' ':
                    current_x += wall_height
                    radar_current_x += radarwall_height
                else:
                    current_x += wall_width
                    radar_current_x += radarwall_width
            elif s == '_':
                current = (current_x, current_y + wall_width)
                radarcurrent = (radar_current_x, radar_current_y + radarwall_width)
                if not(outer_char or outer_line):
                    Wall(current, radarcurrent, 'landscape')
                else:
                    OuterWall(current, radarcurrent, 'landscape')
                radar_current_x += radarwall_width
                current_x += wall_width
            elif s == '.':
                current = (current_x, current_y + wall_width)
                radarcurrent = (radar_current_x, radar_current_y + radarwall_width)
                if not(outer_char or outer_line):
                    Wall(current, radarcurrent, 'adapter')
                else:
                    OuterWall(current, radarcurrent, 'adapter')
                radar_current_x += radarwall_height
                current_x += wall_height
            elif s == '|':
                current_1 = (current_x, current_y)
                radarcurrent_1 = (radar_current_x, radar_current_y)
                current_2 = (current_x, current_y + wall_width)
                radarcurrent_2 = (radar_current_x, radar_current_y + radarwall_width)
                if not outer_char:
                    Wall(current_1, radarcurrent_1, 'portrait')
                    Wall(current_2, radarcurrent_2, 'adapter')
                    current_x += wall_height
                else:
                    OuterWall(current_1, radarcurrent_1, 'portrait')
                    OuterWall(current_2, radarcurrent_2, 'adapter')
                    current_x += wall_height
                radar_current_x += radarwall_height
                
            if last_char==s and s ==' ':
                last_char = None
            else:
                last_char = s

        radar_current_y += radarwall_width
        current_y += wall_width
        
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
def enemy_move(receive_data):
    for enemy in enemy_list:
        if enemy['session_id'] == receive_data['session_id']:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']

#敵が発射した時に初期位置と方向,弾IDをリストに追加
def enemy_fire(receive_data):
    for enemy in enemy_list:
        if enemy['session_id'] == receive_data['session_id']:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']
            enemy['obj'].fire(receive_data['speed'],receive_data['bullet_id'],
                              receive_data['colid_point'])

#敵が被弾したと申告してきた時にHPを合わせて,弾IDを削除リストに追加
def enemy_struck(receive_data):
    for enemy in enemy_list:
        if enemy['session_id'] == receive_data['session_id']:
            enemy['obj'].hp = receive_data['hp']
            enemy['obj'].struck()
            
    bullet_id = receive_data['bullet_id']
    struckted_bullet_list.append((bullet_id,
                                receive_data['x'],
                                receive_data['y']))
    #自分が発射した弾が命中した時
    if bullet_id in fired_bullet_list:
        fired_bullet_list.remove(bullet_id)
        #当てた機体が死んでなかった時のみ得点
        if not bool(receive_data['died']):
            hit()
    elif bullet_id in bombed_list:
        if not bool(receive_data['died']):
            bombhit()
            
#敵が爆弾を置いた場合
def enemy_bomb(receive_data):
    for enemy in enemy_list:
        if enemy['session_id'] == receive_data['session_id']:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].bombed(receive_data['explode'], receive_data['bullet_id'])
        
#命中時
def hit():
    global score
    score += bullet_damage
    
def bombhit():
    global score
    score += bullet_damage * 10

#初期位置の候補をランダムに
def init_place(field_x, field_y, wall_width):
    start_x = random.randint(wall_width, field_x - wall_width)
    start_y = random.randint(wall_width, field_y - wall_width)
    
    return start_x, start_y

#正確な現在時刻
def nowtime():
    return time.time() + time_offset

class TankSelect(object):
    def __init__(self, x, y, image, speed, hp, attack, accel):
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        #説明テキスト用
        color = (255, 255, 255)
        font = pygame.font.Font('ipagp.ttf', 20)
        self.label_init_x = self.rect.topright[0] + 10
        self.label_init_y = self.rect.topright[1]
        self.hp_label = font.render(u'HP: {}'.format(hp), True, color)
        self.speed_label = font.render(u'最高速度: {}'.format(speed), True, color)
        self.attack_label = font.render(u'攻撃力: {}'.format(attack), True, color)
        self.accel_label = font.render(u'加速力: {}'.format(accel), True, color)
        
        
    def update(self):
        screen.blit(self.image, self.rect)
        #tank情報表示
        screen.blit(self.hp_label, (self.label_init_x,self.label_init_y))
        screen.blit(self.speed_label, (self.label_init_x,self.label_init_y+25))
        screen.blit(self.attack_label, (self.label_init_x,self.label_init_y+50))
        screen.blit(self.accel_label, (self.label_init_x,self.label_init_y+75))


def place_select_tank(tank_types, num_tank_row, tank_dataset):
    #配置する間隔
    x_step = screen_width /4
    current_y = 300
    select_tanks = list()
    current_tank_id = 0
    for i in range(tank_types/num_tank_row):
        for n in range(num_tank_row):
            current_x = (n+1)*x_step
            image = tank_id_file[current_tank_id]
            tank_data = tank_dataset[current_tank_id]
            speed = int(tank_data['tank_speed'])
            hp = tank_data['hp']
            attack = tank_data['bullet_damage']
            accel = tank_data['accel_ratio']
            select_tanks.append(TankSelect(current_x, current_y, image, speed, hp, attack, accel))
            current_tank_id += 1
        current_y += 200
        
    return select_tanks
        

if __name__ == '__main__':
    #debug
    if raw_input('localhost?(y)> ')=='y':
        debug = True
        server_addr = '127.0.0.1:5000'
        receive_port = int(raw_input('RECV PORT> '))
    else:
        server_addr = raw_input('ServerAddr> ')
        debug = False
        receive_port = 8800
    
    screen_width = 1024
    screen_height = 768
    #tank_idに対応したファイル名
    tank_id_file = ('./imgs/0_tank.png','./imgs/1_tank.png','./imgs/2_tank.png','./imgs/3_tank.png',
                    './imgs/4_tank.png','./imgs/5_tank.png')
    diedtank_id_file = ('./imgs/0_tank_died.png','./imgs/1_tank_died.png','./imgs/2_tank_died.png','./imgs/3_tank_died.png',
                    './imgs/4_tank_died.png','./imgs/5_tank_died.png')
    bullet_id_file = ('./imgs/0_bullet.png','./imgs/1_bullet.png','./imgs/2_bullet.png','./imgs/3_bullet.png',
                      './imgs/4_bullet.png','./imgs/5_bullet.png')
    
    #フィールドサイズ
    maze_x = 10
    maze_y = 10
    
    screen = pygame.display.set_mode([screen_width, screen_height])

    pygame.display.set_caption('GTO -Gun Tank Online-')
    clock = pygame.time.Clock()
    
    #時刻の差と自IPアドレスを取得
    server_time, my_ipaddr = json.loads(urllib2.urlopen('http://{}/time'.format(server_addr)).read())
    time_offset = float(server_time) - time.time()

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
    hp_died_img = pygame.image.load('./imgs/hpdied.png').convert_alpha()
    #HP/名前の背景
    statusback_img = pygame.image.load('./imgs/statusback.png').convert_alpha()
    #自機ステータス
    mystatusback_img = pygame.image.load('./imgs/mystatusback.png').convert_alpha()
    mystatus_x = screen_width - 410
    mystatus_y = screen_height - 190
    myhp_green_img = pygame.image.load('./imgs/myhp_green.png').convert()
    myhp_red_img = pygame.image.load('./imgs/myhp_red.png').convert()
    myhpbarback_img = pygame.image.load('./imgs/myhpback.png').convert()
    mybombbar_img = pygame.image.load('./imgs/mybombbar.png').convert()
    
    #爆発アニメ
    explode_anim_imgs = [pygame.image.load('./imgs/explode/{}.png'.format(n)).convert_alpha() for n in range(15)]
    smallexplode_anim_imgs = [pygame.image.load('./imgs/small_explode/{}.png'.format(n)).convert_alpha() for n in range(15)]
    bombanim_imgs = [pygame.image.load('./imgs/bomb/{}.gif'.format(n)).convert_alpha() for n in range(2)]
    bombexplodeanim_imgs = [pygame.image.load('./imgs/bomb_explode/{}.png'.format(n)).convert_alpha() for n in range(15)]

    #送受信データキュー,送受信プロセス作成
    send_queue = Queue()
    receive_queue = Queue()
    send_process = Process(target=send, args=(send_queue,))
    receive_process = Process(target=receive, args=(receive_queue, receive_port))
    send_process.start()
    receive_process.start()
    
    title_font = pygame.font.Font('ipagp.ttf',70)
    tankname_font = pygame.font.Font('ipagp.ttf', 20)
    mystatus_font = pygame.font.Font('ipagp.ttf', 30)
    myhp_descript =  mystatus_font.render('HP', True, (255,255,255))
    mybomb_descript =  mystatus_font.render('BOMB', True, (255,255,255))
    score_font = pygame.font.Font('ipagp.ttf', 40)
    waitmessage_font = pygame.font.Font('ipagp.ttf',40)
    waitsecs_font = pygame.font.Font('ipagp.ttf',200)
    countdown_font = pygame.font.Font('ipagp.ttf',500)
    start_font = pygame.font.Font('ipagp.ttf',300)
    ranking_font = pygame.font.Font('ipagp.ttf',20)
    
    
    #テキストボックス
    input_entered = None
    textbox_width = 300
    textbox_height = 75
    btn_width = 900
    btn_height = 100
    
    title_surface = title_font.render(u'GunTankOnline',True,(255,255,255))
    top_guestbtn = Button(u'ゲストとして参戦', pygame.Rect(0,400,btn_width, btn_height))
    top_guestbtn.rect.centerx = screen.get_rect().centerx
    top_loginbtn = Button(u'ログインして参戦', pygame.Rect(0,550,btn_width, btn_height))
    top_loginbtn.rect.centerx = screen.get_rect().centerx
    login_loginbtn = Button(u'ログイン', pygame.Rect(0, 600, btn_width, btn_height))
    login_loginbtn.rect.centerx = screen.get_rect().centerx
    login_backbtn = Button(u'戻る', pygame.Rect(0, 600, btn_width, btn_height))
    login_backbtn.rect.left = screen.get_rect().left + 50
    
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
                damagedwalls = pygame.sprite.RenderUpdates()
                DamagedWall.containers = all_sprites, damagedwalls
                bullets = pygame.sprite.RenderUpdates()
                Bullet.containers = all_sprites, bullets
                radarwalls = pygame.sprite.RenderUpdates()
                RadarWall.containers = all_sprites, radarwalls
                radartanks = pygame.sprite.RenderUpdates()
                RadarTank.containers = all_sprites, radartanks
                explodes = pygame.sprite.RenderUpdates()
                Explode.containers = all_sprites, explodes
                grounds = pygame.sprite.RenderUpdates()
                Ground.containers = all_sprites, grounds
                outergrounds = pygame.sprite.RenderUpdates()
                OuterGround.containers = all_sprites, outergrounds
                bombs = pygame.sprite.RenderUpdates()
                Bomb.containers = all_sprites, bombs
                craters = pygame.sprite.RenderUpdates()
                Crater.containers = all_sprites, craters
                
                #敵が被弾した弾リスト初期化
                struckted_bullet_list = list()
                
                #自分が打った弾リスト
                fired_bullet_list = list()
                bombed_list = list()
                
                tank_dataset = json.loads(urllib2.urlopen('http://{}/tankdata'.format(server_addr)).read())
                
                state = 'title'

            #タイトル画面
            elif state == 'title':
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        #ゲスト参戦クリック
                        if top_guestbtn.rect.collidepoint(pygame.mouse.get_pos()):
                            select_tanks = place_select_tank(6, 3, tank_dataset)
                            user_id = None
                            password = None
                            state = 'select'
                        #ログイン参戦クリック
                        elif top_loginbtn.rect.collidepoint(pygame.mouse.get_pos()):
                            textboxes = [
                                TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200,300,75),1),
                                TextBox(pygame.Rect(screen_width/2-textbox_width/2,screen_width/2-200+textbox_height*2,300,75),1)]
                            state = 'login'

                    screen.fill((0,0,0))
                    title_rect = title_surface.get_rect()
                    title_rect.center = (screen_width/2, 50)
                    screen.blit(title_surface, title_rect)
                    top_guestbtn.update(screen)
                    top_loginbtn.update(screen)
                    
            elif state == 'login':
                screen.fill((0,0,0))
                color = (255,255,255)
                screen.blit(title_surface, title_rect)
                page_name = u'ログイン'
                page_surface = title_font.render(page_name, True, color)
                screen.blit(page_surface, title_rect.midbottom)
                
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        for box in textboxes:
                            if box.selected:
                                input_entered = box.char_add(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1 and state=='login':
                            for box in textboxes:
                                if box.rect.collidepoint(pygame.mouse.get_pos()):
                                    box.selected = True
                                else:
                                    box.selected = False
                                if login_loginbtn.rect.collidepoint(pygame.mouse.get_pos()):
                                    id_input = textboxes[0].string
                                    pass_input = textboxes[1].string
                                    if id_input and pass_input:
                                        user_id = id_input
                                        password = pass_input
                                        state = 'auth'
                                        select_tanks = place_select_tank(6, 3, tank_dataset)
                                        
                                elif login_backbtn.rect.collidepoint(pygame.mouse.get_pos()):
                                    state = 'init'
                                    

                                        
                for box in textboxes:
                    box.update(screen)
                login_loginbtn.update(screen)
                login_backbtn.update(screen)
                
            elif state == 'auth':
                data = json.loads(urllib2.urlopen(
                                'http://{}/user?id={}&pass={}'.format(server_addr,user_id,password)).read())
                if data['auth'] == False:
                    print('Auth fail')
                    state = 'init'
                else:
                    print('score: {}'.format(data['userdat'][1]))
                    state = 'select'

            #機体選択
            elif state == 'select':
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        #ゲスト参戦クリック
                        for i,select_tank in enumerate(select_tanks):
                            if select_tank.rect.collidepoint(pygame.mouse.get_pos()):
                                mytank_id = i
                                state = 'attend'
                        if login_backbtn.rect.collidepoint(pygame.mouse.get_pos()):
                            state = 'init'

                screen.fill((0,0,0))
                color = (255,255,255)
                screen.blit(title_surface, title_rect)
                page_name = u'機体セレクト'
                page_surface = title_font.render(page_name, True, color)
                screen.blit(page_surface, title_rect.midbottom)
                [select_tank.update() for select_tank in select_tanks]
                #戻るボタン
                login_backbtn.update(screen)

            #参戦選択後の処理
            elif state == 'attend':
                #自機データ送信,セッションID取得
                if user_id:
                    data = {'ipaddr':my_ipaddr, 'port':receive_port, 'tank_id':mytank_id, 'id':user_id, 'pass':password}
                else:
                    data = {'ipaddr':my_ipaddr, 'port':receive_port, 'tank_id':mytank_id}
                    
                data = json.loads(urllib2.urlopen('http://{}/attend?json={}'.format(server_addr,
                                              urllib2.quote(json.dumps(data)))).read())
                mysession_id = data['session_id']
                myname = data['name']
                #ポーリングで何秒待ってるか
                poll_secs = 0
                state = 'wait'
                    
            elif state == 'wait':
                screen.fill((0,0,0))
                color = (255,255,255)
                screen.blit(title_surface, title_rect)
                page_name = u'マッチング中...'
                page_surface = title_font.render(page_name, True, color)
                screen.blit(page_surface, title_rect.midbottom)
                #フリーズ防止
                pygame.event.get()
                    
                
                if poll_secs <= 0:
                    #サーバから承認されて開始データが来るまで待機
                    data = json.loads(urllib2.urlopen('http://{}/check'.format(server_addr)).read())
                    poll_secs = 3  #デフォルトを3sに
                else:
                    poll_secs -= passed_seconds
                    
                if not data['start']:
                    waitmessage = u'対戦相手が見つかるまで、そのまま離れずにお待ちください'
                    wait_secs = None
                else:
                    waitmessage = u'対戦相手が{}人見つかりました。開始までお待ちください'.format(data['waiting']-1)
                    start_time = data['start_time']
                    battle_id = data['battle_id']
                    battle_duration = data['duration']
                    current_time = nowtime()
                    
                    if start_time < current_time:
                        state = 'start'
                    wait_secs = start_time - current_time
                    waitsecs_surface = waitsecs_font.render(str(int(wait_secs)), True, color)
                    screen.blit(waitsecs_surface, (screen_width/2-waitsecs_surface.get_width()/2 ,screen_height /3 *2))
                        
                waitmessage_surface = waitmessage_font.render(waitmessage, True, color)
                screen.blit(waitmessage_surface, (screen_width/2-waitmessage_surface.get_width()/2,screen_height/2))
                
            elif state == 'start':
                data = json.loads(urllib2.urlopen('http://{}/start?battle_id={}'.format(server_addr, battle_id)).read())
                maze = data[0]
                players = data[1]
                tank_dataset = data[3]

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
                    
                    tank_id = player['tank_id']
                    
                    if session_id == mysession_id:
                        #自機obj生成
                        mytank = Tank(screen_width/2,screen_height/2,'right',
                                    tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage, tank_id, True,
                                    accel_ratio, brake_ratio)
                    else:
                        name = player['name']
                        if not name:
                            name = 'GUEST'
                        #敵obj生成
                        enemy_list.append({
                            'obj':Tank(0,0,'right',tank_speed,bullet_speed,bullet_per_sec,hp,bullet_damage,tank_id),
                            'ipaddr':player['ipaddr'],
                            'port':player['port'],
                            'session_id':player['session_id'],
                            'name':name})

                #画像準備
                wall_landscape = pygame.image.load('./imgs/wall.png').convert()
                wall_portrait = pygame.transform.rotate(wall_landscape, 90)
                outer_wall_landscape = pygame.image.load('./imgs/outer_wall.png').convert()
                outer_wall_portrait = pygame.transform.rotate(outer_wall_landscape, 90)
                adapter_image = pygame.image.load('./imgs/adapter.png').convert()
                outer_adapter_image = pygame.image.load('./imgs/outer_adapter.png').convert()
                ground_image = pygame.image.load('./imgs/ground.png').convert()
                outer_ground_image = pygame.image.load('./imgs/outer_ground.png').convert()
                damagedwall_landscape = pygame.image.load('./imgs/damagedwall.png').convert()
                damagedwall_portrait = pygame.transform.rotate(damagedwall_landscape, 90)
                damagedadapter_image = pygame.image.load('./imgs/damagedadapter.png').convert()
                
                myname_descript = mystatus_font.render(myname, True, (255,255,255))

                field_x, field_y = make_field(maze, maze_x, maze_y)
                make_ground(maze_x, maze_y)
                
                #たまったキーイベントによる開始時の動作を防止
                pygame.event.get()

                #アドレスリスト作成
                addresses = list()
                for enemy in enemy_list:
                    addresses.append([enemy['ipaddr'],int(enemy['port'])])
                    
                score = 0
                
                #カウントダウン終了時刻
                end_countdown = start_time + 5
                block = True
                countdown = True
                finish_screen = False

                #初期位置設定
                while True:
                    #ランダムな位置をゲット
                    start_x, start_y = init_place(field_y, field_y, wall_width)
                    start_x -= screen_width/2
                    start_y -= screen_height/2
                    #start_x,yを反映
                    mytank.relative_x = start_x
                    mytank.relative_y = start_y
                    tanks.update(mytank.relative_x, mytank.relative_y, countdown)
                    walls.update(mytank.relative_x, mytank.relative_y)
                    #接触していない場合はループから離脱
                    if not pygame.sprite.spritecollideany(mytank, walls):
                        break

                #初期位置送信
                send_queue.put({
                        'addresses':addresses,
                        'session_id':mysession_id,
                        'type':'move',
                        'x':mytank.x,
                        'y':mytank.y,
                        'way':mytank.way})    
                    
                print('Start')
                state = 'play'

            #ゲーム中
            elif state == 'play':
                #受信データを確認
                while not receive_queue.empty():
                    receive_data, ipaddr =  receive_queue.get(block=False)
                    if receive_data['type']=='move':
                        enemy_move(receive_data)
                    elif receive_data['type']=='fire':
                        enemy_fire(receive_data)
                    elif receive_data['type'] == 'struck':
                        enemy_struck(receive_data)
                    elif receive_data['type'] == 'bomb':
                        enemy_bomb(receive_data)

                #移動前の位置を格納
                last_relative_x = mytank.relative_x
                last_relative_y = mytank.relative_y

                #各オブジェクトをupdate
                tanks.update(mytank.relative_x, mytank.relative_y, countdown)
                walls.update(mytank.relative_x, mytank.relative_y)
                damagedwalls.update(mytank.relative_x, mytank.relative_y)
                bullets.update(mytank.relative_x, mytank.relative_y)
                grounds.update(mytank.relative_x, mytank.relative_y)
                outergrounds.update()
                craters.update(mytank.relative_x, mytank.relative_y)
                
                #固定obj(壁,アダプタ),他の機体と機体との当たり判定
                if pygame.sprite.spritecollideany(mytank, walls):
                    #プラス方向に移動した場合
                    if last_relative_x < mytank.relative_x:
                        mytank.relative_x -= int(2*(mytank.relative_x - last_relative_x))
                    elif last_relative_x > mytank.relative_x:
                        mytank.relative_x += int(2*(last_relative_x - mytank.relative_x))
                    
                    if last_relative_y < mytank.relative_y:
                        mytank.relative_y -= int(2*(mytank.relative_y - last_relative_y))
                    elif last_relative_y > mytank.relative_y:
                        mytank.relative_y += int(2*(last_relative_y - mytank.relative_y))
                   
                    walls.update(mytank.relative_x, mytank.relative_y)
                    tanks.update(mytank.relative_x, mytank.relative_y, countdown)
                    
                #場外に出た時に強制的に戻す
                if not pygame.sprite.spritecollideany(mytank, grounds):
                    mytank.relative_x = start_x
                    mytank.relative_y = start_y
                    walls.update(mytank.relative_x, mytank.relative_y)
                    tanks.update(mytank.relative_x, mytank.relative_y, countdown)
                    
                #機体が動いた場合に送信
                if last_relative_x != mytank.relative_x or \
                        last_relative_y != mytank.relative_y:
                            send_queue.put({
                                'addresses':addresses,
                                'session_id':mysession_id,
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
                craters.draw(screen)
                bullets.draw(screen)
                damagedwalls.draw(screen)
                walls.draw(screen)
                tanks.draw(screen)
                
                #爆弾アニメを更新・表示
                bombs.update(mytank.relative_x, mytank.relative_y)
                
                #爆発アニメーションを更新/表示
                explodes.update(mytank.relative_x, mytank.relative_y)
                
                #自機死亡・全滅確認
                died_list = list()
                for enemy_data in enemy_list:
                    tankname = enemy_data['name']
                    enemy = enemy_data['obj']
                    
                    if enemy.died:
                        died_list.append(True)
                    else:
                        died_list.append(False)
                    
                    #HP/ネーム背景
                    status_x = enemy.rect.x - 30
                    status_y = enemy.rect.y - 55
                    screen.blit(statusback_img, (status_x, status_y))
                    
                    #ユーザー名描画
                    tankname_surface = tankname_font.render(tankname, True, (255, 255, 255))
                    screen.blit(tankname_surface, (status_x + 10, status_y + 5))
                    
                    #HPバー背景(削れたぶん)
                    if enemy.died:
                        screen.blit(hp_died_img, (status_x + 10, status_y + 30))
                    else:
                        screen.blit(hpback_img, (status_x + 10, status_y + 30))
                    
                    #HPバー
                    hp_percent = (float(enemy.hp) / enemy.default_hp)*100
                    if hp_percent > 40:
                        hpbar_img = hp_green_img
                    else:
                        hpbar_img = hp_red_img
                    #マイナス考慮
                    if not enemy.died:
                        hpbar_length = int((hp_percent/100) * hp_green_img.get_width())
                    else:
                        hpbar_length = 0
                        hpbar_img = hp_died_img
                    screen.blit(hpbar_img, (status_x + 10, status_y + 30),
                                area=pygame.Rect(0, 0, hpbar_length, hp_green_img.get_height()))
                    
                if mytank.died:
                    block = True
                    died_list.append(True)
                else:
                    died_list.append(False)

                #レーダー描画
                screen.blit(radar_img, (radar_init_x, radar_init_y)) #レーダー画面
                radartanks.draw(screen)
                radarwalls.draw(screen)
                
                #自機ステータス表示
                mystatus_rect = mystatusback_img.get_rect()
                mystatus_rect.topleft = (mystatus_x, mystatus_y)
                screen.blit(mystatusback_img, mystatus_rect)
                #自機名前
                screen.blit(myname_descript, (mystatus_x+5, mystatus_y+5))
                #残り秒数,スコア
                if not countdown:
                    resttime = int(battle_starttime+battle_duration-nowtime())
                    if resttime < 0:
                        resttime = 0
                    secscore_surface = mystatus_font.render('{}points/{}sec'.format(score,resttime),True,(255,255,255))
                    secscore_rect = secscore_surface.get_rect()
                    secscore_rect.right = mystatus_rect.right - 5
                    secscore_rect.top = mystatus_rect.top + 40
                    screen.blit(secscore_surface, secscore_rect)
                #自機HP
                screen.blit(myhp_descript, (mystatus_x+5, mystatus_y+90))
                screen.blit(myhpbarback_img, (mystatus_x+105, mystatus_y+90))
                myhp_percent = (float(mytank.hp) / mytank.default_hp)*100
                if myhp_percent > 40:
                    myhpbar_img = myhp_green_img
                else:
                    myhpbar_img = myhp_red_img

                if not mytank.died:
                    myhpbar_length = int((myhp_percent/100) * myhp_green_img.get_width())
                else:
                    myhpbar_length = 0      #マイナスを考慮
                screen.blit(myhpbar_img, (mystatus_x + 105, mystatus_y + 90),
                            area=pygame.Rect(0, 0, myhpbar_length, myhp_green_img.get_height()))
                #自機ボム
                screen.blit(mybomb_descript, (mystatus_x+5, mystatus_y+125))
                screen.blit(myhpbarback_img, (mystatus_x+105, mystatus_y+125))
                try:
                    bomb_ratio = mytank.bomb_passed_sec/mytank.bomb_wait_sec
                    if bomb_ratio>1: bomb_ratio=1
                    mybomb_length = bomb_ratio* myhp_green_img.get_width()
                except ZeroDivisionError:
                    mybomb_length = 0
                screen.blit(mybombbar_img, (mystatus_x + 105, mystatus_y + 125),
                            area=pygame.Rect(0, 0, mybomb_length, myhp_green_img.get_height()))
                
                
                
                #開始カウントダウン
                if countdown:
                    count_sec =  str(int(end_countdown - nowtime()))
                    if count_sec == '0':
                        count_sec = 'START'
                        battle_starttime = nowtime()
                        #接続失敗ノードの切り離し
                        for enemy_data in enemy_list:
                            enemy = enemy_data['obj']
                            if enemy.default_x==0 and enemy.default_y==0:
                                radartanks.remove(enemy.radar)
                                all_sprites.remove(enemy.radar)
                                tanks.remove(enemy)
                                all_sprites.remove(enemy)
                                enemy_list.remove(enemy_data)
                        block = False
                        countdown = False
                    s = pygame.Surface((screen_width, screen_height), SRCALPHA)
                    s.fill((255,255,255,128))
                    screen.blit(s, (0,0))
                    if count_sec == 'START':
                        count_sec_surface = start_font.render(count_sec, True, (255,255,255))
                    else:
                        count_sec_surface = countdown_font.render(count_sec, True, (255,255,255))
                    screen.blit(count_sec_surface, (screen_width/2-count_sec_surface.get_width()/2,
                                                    screen_height/2-count_sec_surface.get_height()/2))
                    
                #自機を含めて誰か一人だけになったか終了時刻の場合は終了
                if not countdown and (died_list.count(False)<=1 or battle_starttime+battle_duration <= nowtime()):
                    if not finish_screen:
                        block = True
                        s = pygame.Surface((screen_width, screen_height), SRCALPHA)
                        s.fill((0,0,0,128))
                        finish_surface = start_font.render('FINISH', True, (255,255,255))
                        screen.blit(finish_surface, (screen_width/2-count_sec_surface.get_width()/2,
                                    screen_height/2-count_sec_surface.get_height()/2))
                        end_display_finish = nowtime() + 5
                        screen.blit(s, (0,0))
                        screen.blit(finish_surface, (screen_width/2-count_sec_surface.get_width()/2,
                                    screen_height/2-count_sec_surface.get_height()/2))
                        #スコアアップロード
                        if not mytank.died:
                            mytank.deadtime = 2147483647 #max
                        urllib2.urlopen('http://{}/score?battle_id={}&session_id={}&score={}&deadtime={}'.format(
                            server_addr, battle_id, mysession_id, score, mytank.deadtime))
                        finish_screen = True
                        
                    else:
                        screen.blit(s, (0,0))
                        screen.blit(finish_surface, (screen_width/2-count_sec_surface.get_width()/2,
                                    screen_height/2-count_sec_surface.get_height()/2))
                        if nowtime() > end_display_finish:
                            print('Finished')
                            data = json.loads(urllib2.urlopen('http://{}/ranking?battle_id={}'.format(
                                                server_addr, battle_id)).read())
                            sorted_session = sorted(data, key=lambda session: session['score'], reverse=True)
                            exitbtn = Button(u'終了', pygame.Rect(0,550,btn_width, btn_height))
                            exitbtn.rect.centerx = screen.get_rect().centerx
                            state = 'result'
                    
                    
            elif state=='result':
                screen.fill((0,0,0))
                color = (255,255,255)
                screen.blit(title_surface, title_rect)
                page_name = u'リザルト'
                page_surface = title_font.render(page_name, True, color)
                screen.blit(page_surface, title_rect.midbottom)
                
                current_x = 50
                current_y = 200
                for i,session in enumerate(sorted_session):
                    if not session['score']==-1:
                        rank_text = u'第{}位:  {}  {}points'.format(i+1,session['name'],session['score'])
                    else:
                        rank_text = u'第{}位:  {}  DISCONNECTED'.format(i+1,session['name'])
                    rank_surface = ranking_font.render(rank_text, True, color)
                    screen.blit(rank_surface, (current_x, current_y))
                    current_y += 30
                    
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        #クリック
                        if exitbtn.rect.collidepoint(pygame.mouse.get_pos()):
                            state = 'init'
                
                exitbtn.update(screen)
                    
            pygame.display.update()
            clock.tick(30)
            
        #終了
        except KeyboardInterrupt:
            pygame.quit()
            send_process.terminate()
            receive_process.terminate()
            print('quit')
            exit()