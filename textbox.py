#coding:utf-8
import pygame

class TextBox:
    def __init__(self, rect, width=1):
        self.selected = False
        self.font_size = 60
        self.font = pygame.font.Font('ipagp.ttf',self.font_size)
        self.str_list = []
        self.width = width
        self.color = (255,255,255)
        self.rect = rect
        self.string = ''.join(self.str_list)
       
    def char_add(self, event):
        '''modify string list based on event.key'''
        if event.key == pygame.K_BACKSPACE:
            if self.str_list:
                self.str_list.pop()
        elif event.key == pygame.K_RETURN:
            return ''.join(self.str_list)
        elif event.key in [pygame.K_TAB, pygame.K_KP_ENTER]:#unwanted keys
            return False
        elif event.key == pygame.K_DELETE:
            self.str_list = []
            return False
        else:
            char = event.unicode
            if char: #stop emtpy space for shift key adding to list
                self.str_list.append(char)

    def update(self, scr):
       
        if self.selected:
            width = 2
        else:
            width = self.width
       
        s = ''.join(self.str_list)
        if len(s) > 0:
            for n, l in enumerate(s):
                if self.font.size(s[n:])[0] < self.rect.width:
                    label = self.font.render(s[n:], 1, self.color)
                    break
        else:
            label = self.font.render(s, 1, self.color)
       
        self.string = ''.join(self.str_list)
        pygame.draw.rect(scr, self.color, self.rect, width)
        scr.blit(label, self.rect)
       
class Button:
    def __init__(self, text, rect):
        self.text = text
        self.is_hover = False
        self.default_color = (150,150,150)
        self.hover_color = (255,255,255)
        self.font_color = (0,0,0)
        self.rect = rect
       
    def label(self):
        '''button label font'''
        font = pygame.font.Font('ipagp.ttf', 90)
        return font.render(self.text, 1, self.font_color)
       
    def color(self):
        '''change color when hovering'''
        if self.is_hover:
            return self.hover_color
        else:
            return self.default_color
           
    def update(self, screen):
        pygame.draw.rect(screen, self.color(), self.rect)
        screen.blit(self.label(), self.rect)
       
        #change color if mouse over button
        self.check_hover(pygame.mouse.get_pos())
       
    def check_hover(self, mouse):
        '''adjust is_hover value based on mouse over button - to change hover color'''
        if self.rect.collidepoint(mouse):
            self.is_hover = True
        else:
            self.is_hover = False

