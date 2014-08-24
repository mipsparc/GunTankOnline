#coding:utf-8
import pygame
from pygame.locals import *
from maze_generator import Maze
import socket
import json
from multiprocessing import Process,Queue
from Queue import Empty
import time
import random


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, way, speed, bullet_speed, bullet_per_sec,
            hp, bullet_power, relative_x=None, relative_y=None, center=None):
        #setting sprite group
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.clock = pygame.time.Clock()
        self.clock.tick()

        self.center = center

        self.origin_image = pygame.image.load('tank.png').convert_alpha()
        self.width = self.origin_image.get_width()
        self.height = self.origin_image.get_height()
        self.rect = self.origin_image.get_rect()

        self.hp = hp
        self.way = way
        self.speed = speed
        self.bullet_speed = bullet_speed
        self.bullet_per_sec = bullet_per_sec
        self.bullet_power = bullet_power

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
            self.rect.x = self.default_x - relative_x
            self.rect.y = self.default_y - relative_y

    def update(self, relative_x=None, relative_y=None):
        if self.center:
            passed_seconds = self.clock.tick()/1000.0

            x_diff = 0
            y_diff = 0

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
            if pressed_keys[K_x] and \
                    self.bullet_passed_sec * self.bullet_per_sec >= 1:
                if x_diff or y_diff:
                    self.fire(self.speed + self.bullet_speed)
                else:
                    self.fire(self.bullet_speed)
                self.bullet_passed_sec = 0

            self.relative_x += x_diff
            self.relative_y += y_diff
            self.x = relative_x + screen_width/2
            self.y = relative_y + screen_height/2

        else:
            self.rect.x = self.default_x - relative_x
            self.rect.y = self.default_y - relative_y

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
            Bullet(self, speed, bullet_id)
            send_queue.put({
                'type':'fire',
                'time':time.time(),
                'x':self.x,
                'y':self.y,
                'way':self.way,
                'bullet_id':bullet_id,
                'speed':speed
                })
        else:
            Bullet(self, speed,bullet_id)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, tank, speed, bullet_id):
        pygame.sprite.Sprite.__init__(self, self.containers)

        self.clock = pygame.time.Clock()
        self.clock.tick()

        self.bullet_id = bullet_id

        self.origin_image = pygame.image.load('bullet.png').convert_alpha()
        bullet_check_length = 2000

        if tank.way == 'up':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width/2
                self.default_y = screen_height/2 + tank.relative_y
            else:
                self.default_x = tank.default_x + tank.width/2
                self.default_y = tank.default_y
            self.image = pygame.transform.rotate(self.origin_image, 90)
            move_rect = pygame.Rect(self.default_x,
                    self.default_y - bullet_check_length,
                    self.image.get_width(),
                    self.image.get_height() + bullet_check_length)
        elif tank.way == 'down':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width/2
                self.default_y = screen_height/2 + tank.relative_y + tank.width
            else:
                self.default_x = tank.default_x + tank.width/2
                self.default_y = tank.default_y + tank.width
            self.image = pygame.transform.rotate(self.origin_image, 270)
            move_rect = pygame.Rect(self.default_x,
                    self.default_y,
                    self.image.get_width(),
                    self.image.get_height() + bullet_check_length)
        elif tank.way == 'left':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x
                self.default_y = screen_height/2 + tank.relative_y + tank.height/2
            else:
                self.default_x = tank.default_x
                self.default_y = tank.default_y + tank.height/2
            self.image = pygame.transform.rotate(self.origin_image, 180)
            move_rect = pygame.Rect(self.default_x - bullet_check_length,
                    self.default_y,
                    self.image.get_width() + bullet_check_length,
                    self.image.get_height())
        elif tank.way == 'right':
            if tank.center:
                self.default_x = screen_width/2 + tank.relative_x + tank.width
                self.default_y = screen_height/2 + tank.relative_y + tank.height/2
            else:
                self.default_x = tank.default_x + tank.width
                self.default_y = tank.default_y + tank.height/2
            self.image = self.origin_image
            move_rect = pygame.Rect(self.default_x,
                    self.default_y,
                    self.image.get_width() + bullet_check_length,
                    self.image.get_height())

        self.rect = self.image.get_rect()
        self.way = tank.way
        self.speed = speed

        def dummysprite(self):
            pass
        dummysprite.rect = move_rect
        hit_wall_x_list = list()
        hit_wall_y_list = list()
        for collidesprite in pygame.sprite.spritecollide(dummysprite, walls,
                False):
            hit_wall_x_list.append(collidesprite.default_x)
            hit_wall_y_list.append(collidesprite.default_y)
        if tank.way == 'up':
            self.hit_wall_y = max(hit_wall_y_list)
        elif tank.way == 'down':
            self.hit_wall.y = min(hit_wall_y_list)
        elif tank.way == 'left':
            self.hit_wall_x = max(hit_wall_x_list)
        elif tank.way == 'right':
            self.hit_wall_x = min(hit_wall_x_list)
        print hit_wall_x_list,hit_wall_y_list
        print move_rect
                
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

        if ((self.way == 'up' or self.way == 'down') \
                and self.hit_wall_y <= self.default_y) \
                or ((self.way == 'left' or self.way == 'right') \
                and self.hit_wall_x <= self.default_x):
            all_sprites.remove(self)
            bullets.remove(self)
            print 'removed'

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
        self.wall_landscape = pygame.image.load('wall.png').convert()
        self.wall_portrait = pygame.transform.rotate(self.wall_landscape, 90)


class OuterWall(Wall):
    def get_img(self):
        self.wall_landscape = pygame.image.load('outer_wall.png').convert()
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
        self.adapter_image = pygame.image.load('adapter.png').convert()


class OuterAdapter(Adapter):
    def get_img(self):
        self.adapter_image = pygame.image.load('outer_adapter.png').convert()


def make_field(wall_width, wall_height, adapter_width, adapter_height):
    maze_x = 10
    maze_y = 10
    field_x = (wall_width + wall_height) * maze_x - wall_height
    field_y = (wall_width + wall_height) * maze_y - wall_height
    maze = Maze(maze_x, maze_y).__str__()
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


def send(send_queue, ipaddr_list, send_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            send_data = send_queue.get(block=False)
        except Empty:
            pass
        else:
            for ipaddr in ipaddr_list:
                sock.sendto(json.dumps(send_data), (ipaddr, send_port))
        time.sleep(0.02)

def receive(receive_queue, receive_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('',receive_port))

    while True:
        data, addr = sock.recvfrom(4096)
        ipaddr, recv_port = addr
        receive_queue.put((json.loads(data),ipaddr))

def enemy_move(receive_data, ipaddr):
    for enemy in enemy_list:
        if enemy['ipaddr'] == ipaddr:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']

def enemy_fire(receive_data, ipaddr):
    for enemy in enemy_list:
        if enemy['ipaddr'] == ipaddr:
            enemy['obj'].default_x = receive_data['x']
            enemy['obj'].default_y = receive_data['y']
            enemy['obj'].way = receive_data['way']
            enemy['obj'].fire(receive_data['speed'],receive_data['bullet_id'])


if __name__ == '__main__':
    port = 8800

    enemy_ipaddr = raw_input('EnemyIPaddr> ')
    if enemy_ipaddr == '127.0.0.1' or enemy_ipaddr == 'lo':
        enemy_ipaddr = '127.0.0.1'
        cli_num = int(raw_input('CliNum> '))
        if cli_num == 1:
            send_port = port
            receive_port = port + 1
        elif cli_num == 2:
            send_port = port +1
            receive_port = port
    else:
        send_port = port
        receive_port = port

    screen_width = 1024
    screen_height = 768
    pygame.init()
    screen = pygame.display.set_mode([screen_width, screen_height])

    pygame.display.set_caption('tank')
    clock = pygame.time.Clock()

    enemy_bullet_list = list()

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

    wall_width = pygame.image.load('wall.png').get_width()
    wall_height = pygame.image.load('wall.png').get_height()
    adapter_height = pygame.image.load('adapter.png').get_height()
    adapter_width = pygame.image.load('adapter.png').get_width()

    make_field(wall_width, wall_height, adapter_width, adapter_height)

    mytank = Tank(screen_width/2, screen_height/2, 'right', 300, 500, 2, 300,
            50, center=True)
    enemy_tank = Tank(0, 0, 'left', 300, 500, 2, 300, 50, mytank.relative_x,
            mytank.relative_y)

    enemy_list = [
                {'obj':enemy_tank,
                'ipaddr':enemy_ipaddr,
                },]
    ipaddr_list = list()
    for enemy in enemy_list:
        ipaddr_list.append(enemy['ipaddr'])

    send_queue = Queue()
    receive_queue = Queue()
    send_process = Process(target=send, args=(send_queue, ipaddr_list, send_port))
    receive_process = Process(target=receive, args=(receive_queue, receive_port))
    send_process.start()
    receive_process.start()

    time_delay = 0

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True

        time_passed = clock.tick(30)
        passed_seconds = time_passed / 1000.0

        #receive enemy point
        while not receive_queue.empty():
            receive_data, ipaddr =  receive_queue.get(block=False)
            if receive_data['type']=='move':
                enemy_move(receive_data, ipaddr)
            elif receive_data['type']=='fire':
                enemy_fire(receive_data, ipaddr)
                

        last_relative_x = mytank.relative_x
        last_relative_y = mytank.relative_y

        tanks.update(mytank.relative_x, mytank.relative_y)
        walls.update(mytank.relative_x, mytank.relative_y)
        adapters.update(mytank.relative_x, mytank.relative_y)
        bullets.update(mytank.relative_x, mytank.relative_y)
        #固定obj当たり判定
        if pygame.sprite.spritecollideany(mytank, walls) or \
                pygame.sprite.spritecollideany(mytank, adapters):
            mytank.relative_x = last_relative_x
            mytank.relative_y = last_relative_y
            walls.update(mytank.relative_x, mytank.relative_y)
            adapters.update(mytank.relative_x, mytank.relative_y)

        if last_relative_x != mytank.relative_x or \
                last_relative_y != mytank.relative_y:
                    send_queue.put({
                            'type':'move',
                            'x':mytank.x,
                            'y':mytank.y,
                            'way':mytank.way})

        screen.fill([255, 255, 255])
        all_sprites.draw(screen)
        pygame.display.update()
        clock.tick(30)

    pygame.quit()
