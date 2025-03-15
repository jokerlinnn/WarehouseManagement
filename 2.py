#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/2 下午9:56
# @Author  : Joker
# @Email   : 284791960@qq.com
# @File    : 2.py
# @Software: PyCharm
# a = '1/12'
# b = '0.3'
# c = '10'
## 判断浮点数
# d = float(b)
# print(d)
# ## 判断整数
# e = int(c)
# print(e)
# ## 判断分数
# f = c.split('/')
# for i in f:
#     int(i)

def jugement(num):
    try:
        return int(num)
    except:
        try:
            float(num)
            return num
        except:
            try:
                f = num.split('/')
                for i in f:
                    int(i)
                return num
            except:
                print('输入的参数有误')


# print(jugement('11/3'))


# a = 1/12
# b = 1 / 12
# print(a + b)
# print(1/6 * 6)

# 取模，Python中可直接用%，计算模，r = a % b
def mod(a, b):
    '''
    :param a: 分子
    :param b: 分母
    :return: 整除，余
    '''
    c = a // b
    r = a - c * b
    return c,r
from decimal import Decimal
from fractions import Fraction
a = Fraction('83/420')
b = Fraction('5/12')
print(a-b + 1)