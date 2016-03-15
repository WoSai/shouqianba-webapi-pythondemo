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


class Bunch(dict):
    """
    >>> d1 = dict(username='admin', password=123456, data={'code': 7788})
    >>> bunch = Bunch(d1)
    >>> bunch.username == d1['username']
    True
    >>> bunch.data.code == 7788
    True
    >>> bunch.name = 'hello'
    """

    def __getattr__(self, item):
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            try:
                value = super(Bunch, self).__getitem__(item)
            except KeyError:
                raise AttributeError('attribute named %s was not found' % item)
            else:
                if isinstance(value, dict):
                    return Bunch(value)
                return value

    def __setattr__(self, key, value):
        super(Bunch, self).__setitem__(key, value)


def md5_str(content):
    """
    计算字符串的MD5值
    :param content:输入字符串
    :return:
    """
    m = hashlib.md5(content.encode('utf-8'))
    return m.hexdigest()
