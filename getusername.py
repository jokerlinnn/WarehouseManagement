#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/5 下午9:25
# @Author  : Joker
# @Email   : 284791960@qq.com
# @File    : getusername.py
# @Software: PyCharm
import getpass
import platform
username = getpass.getuser()
osname = platform.system()
print(username,osname)