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
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import time
import getpass
import platform
username = getpass.getuser()
osname = platform.system()

def nowtime():
    return time.strftime("%Y.%m.%d_%H.%M.%S",time.localtime())
def update_db():
    try:
        secret_id = ''      # 替换为用户的 secretId(登录访问管理控制台获取)
        secret_key = ''      # 替换为用户的 secretKey(登录访问管理控制台获取)
        region = 'ap-chongqing'     # 替换为用户的 Region
        token = None                # 使用临时密钥需要传入 Token，默认为空，可不填
        scheme = 'https'            # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
        # 2. 获取客户端对象
        client = CosS3Client(config)
        # 参照下文的描述。或者参照 Demo 程序，详见 https://github.com/tencentyun/cos-python-sdk-v5/blob/master/qcloud_cos/demo.py
        #
        #### 高级上传接口（推荐）
        # 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
        response = client.upload_file(
           Bucket='warehouse-management-1300436032',
           LocalFilePath='WarehouseManagement.db',
           Key='WarehouseManagement_{}_{}_{}.db'.format(osname,username,nowtime()),
           PartSize=1,
           MAXThread=10,
           EnableMD5=False
        )
        if response['ETag'] :
            return True
        else:
            return False
    except:
        return False



    # print(response)
    # print(response['ETag'])
