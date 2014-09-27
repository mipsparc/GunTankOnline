#coding:utf-8
import wx

application = wx.App()
screen_width = 1024
screen_height = 768
frame = wx.Frame(None,wx.ID_ANY,"GTO -Gun Tank Online-", size=(screen_width, screen_height))

frame.Show()
application.MainLoop()