#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/3 下午8:41
# @Author  : Joker
# @Email   : 284791960@qq.com
# @File    : 3.py
# @Software: PyCharm
import wx
a = True
class MyFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, u'测试面板Panel', size = (600, 300))
        panel = wx.Panel(self)
        button = wx.Button(panel, label = u'关闭', pos = (150, 60), size = (100, 60))
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
    def OnCloseMe(self, event):
        dlg = wx.MessageDialog(None, u"消息对话框测试", u"标题信息", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)
            dlg.Destroy()

if a:
        dial = wx.MessageDialog('自动备份成功', '温馨提示', wx.OK)
        dial.ShowModal()
        dial.Destroy()
else:
        dial = wx.MessageDialog('自动备份失败，请联系管理员', '温馨提示', wx.OK)
        dial.ShowModal()
        dial.Destroy()