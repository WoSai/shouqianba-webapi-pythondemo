# -*- coding: utf-8 -*-


class ServerError(Exception):
    pass


class ClientError(Exception):
    pass


class BizResponseError(Exception):

    def __init__(self, response):
        self.ret_code = response.get('result_code')
        self.err_code = response.get('error_code')
        self.err_msg = response.get('error_message')

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return u"result_code: {}; error_code: {}; error_message: {}".format(self.ret_code, self.err_code, self.err_msg)