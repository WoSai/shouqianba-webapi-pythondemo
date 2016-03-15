# -*- coding: utf-8 -*-

import hashlib
import string
import random


def gen_rand_str(length=8, s_type='mixed', prefix=None, postfix=None):
    """
    生成指定长度的随机数，可设置输出字符串的前缀、后缀字符串
    :param length: 随机字符串长度
    :param s_type:
    :param prefix: 前缀字符串
    :param postfix: 后缀字符串
    :return:
    """
    if s_type == 'digit':
        s = string.digits
    elif s_type == 'ascii':
        s = string.ascii_letters
    elif s_type == 'hex':
        s = '0123456789abcdef'
    else:
        s = string.ascii_letters + string.digits

    ret = []
    mid = [random.choice(s) for _ in xrange(length)]
    if prefix is not None:
        ret.append(prefix)
    ret.extend(mid)
    if postfix is not None:
        ret.append(postfix)
    return ''.join(ret)


def md5_str(content):
    """
    计算字符串的MD5值
    :param content:输入字符串
    :return:
    """
    m = hashlib.md5(content.encode('utf-8'))
    return m.hexdigest()
