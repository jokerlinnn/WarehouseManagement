#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/3 下午8:09
# @Author  : Joker
# @Email   : 284791960@qq.com
# @File    : update_db.py
# @Software: PyCharm
# -*- coding=utf-8
# appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
import time
import getpass
import platform
import os
import shutil
try:
    os.mkdir('backup')
except:
    pass


username = getpass.getuser()
osname = platform.system()

def nowtime():
    return time.strftime("%Y.%m.%d_%H.%M.%S",time.localtime())
def update_db():
    try:

        backup_name = 'backup/WarehouseManagement_{}_{}_{}.db'.format(osname,username,nowtime())
        if shutil.copy('config/WarehouseManagement.db',backup_name):
            return True
        else:
            return False

    except:
        return False



    # print(response)
    # print(response['ETag'])
