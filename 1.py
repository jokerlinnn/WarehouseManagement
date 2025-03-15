#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/8/31 下午2:37
# @Author  : Joker
# @Email   : 284791960@qq.com
# @File    : 1.py
# @Software: PyCharm
import db
#导入sqllite3模块
import sqlite3
def Get_in_out_price(GOOD_NAME):
    # 1.硬盘上创建连接
    con = sqlite3.connect('WarehouseManagement.db')
    # 获取cursor对象
    cur = con.cursor()
    # 执行sql创建表
    sql_id = '''select id from GOODS where GOODS_NAME = '{}'
    '''.format(GOOD_NAME)

    cur.execute(sql_id)
    # 获取所有数据
    id = cur.fetchall()
    # 获取商品id
    goods_id = id[0][0]


    # 入库数量及商品总价
    sql_goods_num_in = '''
    select GOODS_NUM,GOODS_PRICE from STOCK where GOODS_ID = {} and STOCK_TYPE = 1
    '''.format(goods_id)
    cur.execute(sql_goods_num_in)
    _goods_num_in = cur.fetchall()
    # print(_goods_num_in)
    goods_num_in = 0
    Total_price_of_goods = 0
    for i in _goods_num_in:
        goods_num_in = goods_num_in + i[0]
        Total_price_of_goods = Total_price_of_goods + (i[0] *i[1])
    # print(goods_num_in)
    # print(Total_price_of_goods)
    # 入库单价

    # 出库数量
    sql_goods_num_out = '''
    select GOODS_NUM from STOCK where GOODS_ID = {} and STOCK_TYPE = 0
    '''.format(goods_id)
    cur.execute(sql_goods_num_out)
    _goods_num_out = cur.fetchall()
    goods_num_out = 0
    for j in _goods_num_out:
        goods_num_out = goods_num_out + j[0]
    # print(goods_num_out)
    # 关闭游标
    cur.close()
    # 关闭连接
    con.close()
    return goods_num_in,goods_num_out,Total_price_of_goods

print(Get_in_out_price('金龙鱼'))