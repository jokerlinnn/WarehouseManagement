'''
-------------------system module-------------------
'''
import wx
import os
'''
-------------------user module---------------------
'''
import images
from cryptography.fernet import Fernet
from ui.main import MainFrame
from services import userservice

from services.auto_update_db import update_db

class LoginDialog(wx.Dialog):

    def __init__(self):
        super(LoginDialog, self).__init__(None, wx.ID_ANY, title='登录', size=(550, 350))
        # 初始化加密密钥
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        # 初始化界面
        self.InitUI()
        # 窗口居中
        self.Center()
        # 检查是否有保存的账号和密码
        self.load_saved_credentials()
        
    def InitUI(self):
        
        # 控件
        logo_bm = wx.StaticBitmap(self, wx.ID_ANY, images.tee.GetBitmap())
        
        sysname_lb = wx.StaticText(self, wx.ID_ANY, u"拓建公司出入库管理系统")
        sysname_lb.SetFont(wx.Font(18, 70, 90, 92, False, wx.EmptyString))
        account_lb = wx.StaticText(self, wx.ID_ANY, u"账户：")
        password_lb = wx.StaticText(self, wx.ID_ANY, u"密码：")
        version_lb = wx.StaticText(self, wx.ID_ANY, u"v1.0 Created By CTF.Joker.20250315")
        
        self.account_tc = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, size=(150, -1))
        self.account_tc.SetMaxLength(15)
        self.password_tc = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, size=(150, -1), style=wx.TE_PASSWORD)
        self.password_tc.SetMaxLength(15)

        self.save_password_cb = wx.CheckBox(self, wx.ID_ANY, "保存密码")
        self.show_password_cb = wx.CheckBox(self, wx.ID_ANY, "显示密码")
        self.Bind(wx.EVT_CHECKBOX, self.OnShowPassword, self.show_password_cb)

        logon_btn = wx.Button(self, wx.ID_ANY, '登录')
        self.Bind(wx.EVT_BUTTON, self.OnLogin, logon_btn)
    
        # 布局
        bSizer = wx.BoxSizer(wx.VERTICAL)
        
        gbSizer = wx.GridBagSizer(20, 10)
        gbSizer.SetFlexibleDirection(wx.BOTH)
        gbSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        gbSizer.Add(logo_bm, wx.GBPosition(1, 1), wx.GBSpan(4, 1), wx.ALL, 5)
        gbSizer.Add(sysname_lb, wx.GBPosition(1, 2), wx.GBSpan(1, 2), wx.ALL, 5)
        gbSizer.Add(account_lb, wx.GBPosition(2, 2), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(self.account_tc, wx.GBPosition(2, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(password_lb, wx.GBPosition(3, 2), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(self.password_tc, wx.GBPosition(3, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(self.save_password_cb, wx.GBPosition(4, 2), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(self.show_password_cb, wx.GBPosition(4, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        gbSizer.Add(logon_btn, wx.GBPosition(5, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        
        gbSizer.AddGrowableRow(4)
        
        bSizer.Add(gbSizer, 1, wx.EXPAND, 5)
        bSizer.Add(version_lb, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizer(bSizer)

    def OnShowPassword(self, evt):

        current_password = self.password_tc.GetValue()
        sizer = self.password_tc.GetContainingSizer()
        item = sizer.GetItem(self.password_tc)  # 获取 SizerItem 对象
        if item:
            pos = item.GetPos()
            span = item.GetSpan()  # 获取跨度
            flag = item.GetFlag()  # 从 SizerItem 对象中获取标志
            border = item.GetBorder()  # 获取边框值

            # 移除原密码输入框
            sizer.Detach(self.password_tc)
            self.password_tc.Destroy()

            if self.show_password_cb.IsChecked():
                # 创建新的明文输入框
                self.password_tc = wx.TextCtrl(self, wx.ID_ANY, current_password, size=(150, -1))
            else:
                # 创建新的密码输入框
                self.password_tc = wx.TextCtrl(self, wx.ID_ANY, current_password, size=(150, -1), style=wx.TE_PASSWORD)

            # 将新输入框添加到布局中，使用获取的边框值
            sizer.Add(self.password_tc, pos=pos, span=span, flag=flag, border=border)
            self.Layout()


    def OnLogin(self, evt):


        # 输入校验
        username = self.account_tc.GetValue()
        if not username.strip():
            wx.MessageBox("账户不能为空！", "温馨提示", wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            self.account_tc.SetFocus()
            return

        password = self.password_tc.GetValue()
        if not password.strip():
            wx.MessageBox("密码不能为空！", "温馨提示", wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            self.password_tc.SetFocus()
            return
        
        if userservice.auth(username, password) :
            # 保存账号和密码
            if self.save_password_cb.IsChecked():
                self.save_credentials(username, password)

            # 若未勾选保存密码，删除密码文件
            if not self.save_password_cb.IsChecked():
                if os.path.exists('config/credentials.txt'):
                    os.remove('config/credentials.txt')
            self.Close(True)
            frm = MainFrame()
            frm.CenterOnScreen(direction=wx.BOTH)
            frm.Show()
        else:
            wx.MessageBox("用户名或者密码不正确！", "温馨提示", wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            return
        if update_db():
            dial = wx.MessageDialog(self,'自动备份成功', '温馨提示', wx.OK)
            dial.ShowModal()
            dial.Destroy()
        else:
            dial = wx.MessageDialog(self,'自动备份失败，请联系管理员', '温馨提示', wx.OK)
            dial.ShowModal()
            dial.Destroy()

    def save_credentials(self, username, password):
        encrypted_username = self.cipher_suite.encrypt(username.encode())
        encrypted_password = self.cipher_suite.encrypt(password.encode())
        with open('config/credentials.txt', 'wb') as f:
            f.write(self.key + b'\n')
            f.write(encrypted_username + b'\n')
            f.write(encrypted_password)

    def load_saved_credentials(self):
        if os.path.exists('config/credentials.txt'):
            with open('config/credentials.txt', 'rb') as f:
                key = f.readline().strip()
                cipher_suite = Fernet(key)
                encrypted_username = f.readline().strip()
                encrypted_password = f.read().strip()
                username = cipher_suite.decrypt(encrypted_username).decode()
                password = cipher_suite.decrypt(encrypted_password).decode()
                self.account_tc.SetValue(username)
                self.password_tc.SetValue(password)
                self.save_password_cb.SetValue(True)
