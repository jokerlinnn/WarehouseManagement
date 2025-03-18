'''
-------------------system module-------------------
'''
import time

import wx

'''
-------------------user module---------------------
'''
from ui.login import LoginDialog


###添加机器码识别对比
import wmi

def get_cpu_serial():
        """获取CPU序列号"""
        try:
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                        return cpu.ProcessorId.strip()
        except Exception as e:
                print(f"获取CPU序列号时出错: {e}")
        return None

def get_disk_serial():
        """获取硬盘序列号"""
        try:
                c = wmi.WMI()
                for disk in c.Win32_DiskDrive():
                        return disk.SerialNumber.strip()
        except Exception as e:
                print(f"获取硬盘序列号时出错: {e}")
        return None

def generate_hardware_id():
        """生成硬件标识"""
        cpu_serial = get_cpu_serial()
        disk_serial = get_disk_serial()
        if cpu_serial and disk_serial:

                return f"{cpu_serial}-{disk_serial}"
        return None

def is_authorized(authorized_id):
        """验证是否授权"""
        hardware_id = generate_hardware_id()
        # print(hardware_id)
        if hardware_id and hardware_id == authorized_id:
                return True
        return False

def show_info_message():
        app1 = wx.App()
        # 创建一个父窗口，这里用一个简单的框架代替
        frame1 = wx.Frame(None, title="Info Message Example", size=(300, 200))
        # 创建一个消息对话框，设置标题、消息内容和样式
        dlg1 = wx.MessageDialog(frame1, "该设备未授权，请联系管理员", "警告！", wx.OK | wx.ICON_INFORMATION)
        # 显示对话框并等待用户响应
        result = dlg1.ShowModal()
        # 销毁对话框
        dlg1.Destroy()
        app1.MainLoop()



# 预设的授权硬件标识
AUTHORIZED_HARDWARE_ID = "0F8BFBFF000006FB-7177539947044-0"

if is_authorized(AUTHORIZED_HARDWARE_ID):
        pass
        # 这里可以添加你的主程序逻辑
else:
        show_info_message()
        time.sleep(100000)

provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(provider)

if __name__ == '__main__':
        app = wx.App()

        loginDlg = LoginDialog()
        loginDlg.ShowModal()
        loginDlg.Destroy()

        app.MainLoop()
