# -*- coding: utf-8 -*-

import logging
import requests
from urlparse import urljoin
import time
try:
    import simplejson as json
except (ImportError, SyntaxError):
    import json
from .exception import ServerError, ClientError, BizResponseError
from .utils import md5_str, gen_rand_str
import config
import log


def status_code_checker(resp):
    status_code = resp.status_code
    if 200 <= status_code <= 299:
        return True
    elif status_code >= 500:
        raise ServerError(status_code)
    elif status_code == 400:
        raise ClientError("Bad Request")
    elif status_code == 401:
        raise ClientError("Unauthorized Access")
    elif status_code == 403:
        raise ClientError("Forbidden Access")
    elif status_code == 404:
        raise ClientError("Resource Not Found")
    elif status_code == 405:
        raise ClientError("Method Not Allowed")
    elif status_code == 409:
        raise ClientError("Resource Conflict")
    elif status_code == 410:
        raise ClientError("Resource Gone")
    elif status_code == 422:
        raise ClientError("Resource Invalid")
    elif status_code >= 400:
        raise ClientError('status code: %d' % status_code)
    elif status_code in (301, 302, 303, 307):
        raise RuntimeError('Redirection')
    else:
        raise RuntimeError('status code: %d' % status_code)


def result_code_checker(j):
    """
    检查支付网关2.0的响应中最外层的result_code值,当不等于200时抛出异常
    :param j:
    :return:
    """
    if j['result_code'] != '200':
        raise BizResponseError(j)


class BaseClient(object):

    def __init__(self, base_url, **kwargs):
        self.base_url = base_url
        self.response_handlers = [status_code_checker]
        self.json_handlers = []
        self.interceptor = None
        self.logger = logging.getLogger(__name__)
        self.req_kwargs = kwargs.copy()

    def _call_api(self, endpoint, method="post", req_kwargs=None, interceptor=None):
        """
        http调用函数
        :param endpoint: 接口地址,用self.base_url拼接成完整的请求地址
        :param method: http请求方式
        :param req_kwargs: 透传给requests.request的请求参数（不包含url, method）
        :param interceptor: 该参数赋值后,会改变输出值
        :return:
        """
        url = urljoin(self.base_url, endpoint)
        kwargs = self.req_kwargs.copy()
        kwargs.update(req_kwargs)

        self.logger.info("start request", extra=dict(method=method, parameters=kwargs, url=url))
        response = requests.request(method, url, **kwargs)
        self.logger.info("got response", extra=dict(
            response=response.content, status_code=response.status_code,
            elapsed=response.elapsed.microseconds/1000))  # elapsed并非指完整的请求耗时,而是指获取到headers的耗时

        for handler in self.response_handlers:
            handler(response)

        try:
            resp_to_json = response.json()
        except ValueError:
            self.logger.error('convert response to json fail')
            raise
        else:
            for handler in self.json_handlers:
                handler(resp_to_json)

        interceptor = interceptor or self.interceptor
        return response if interceptor is None else interceptor(response, locals().get('resp_to_json', None))


class ShouqianbaClient(BaseClient):

    PAYWAY_ALIPAY = '1'  # 支付宝支付通道,不区分1.0 2.0
    PAYWAY_WECHAT = '3'  # 微信支付通道
    PAYWAY_BAIFUBAO = '4'  # 百度钱包支付通道
    PAYWAY_JD = '5'  # 京东钱包支付通道

    def __init__(self, base_url=None, vendor_sn=None, vendor_key=None, terminal_sn=None, terminal_key=None, **kwargs):
        self.last_order_sn = None
        self._default_goods_subject = "Python Client"
        self.device_id = kwargs.pop('device_id', "50a87771-ca8a-4952-a493-9504c39ab495")  # 设备唯一身份ID
        self.os_info = kwargs.pop("os_info", "Android 5.0")  # 当前系统信息
        self.sdk_version = kwargs.pop("sdk_version", "Python SDK v1.0")  # SDK版本
        self.device_type = kwargs.pop("device_type", "2")  # 设备类型

        self.vendor_sn = vendor_sn or config.vendor_sn
        self.vendor_key = vendor_key or config.vendor_key
        self.terminal_key = terminal_key or config.terminal_key
        self.terminal_sn = terminal_sn or config.terminal_sn

        super(ShouqianbaClient, self).__init__(base_url or config.base_url, **kwargs)
        self.json_handlers.append(result_code_checker)
        self.interceptor = lambda r, j: j

    def _make_signed_request_params(self, is_terminal_activation=False, body=None, **kwargs):
        """
        使用terminal/vendor 的sn, key生成签名,返回requests.request的请求参数
        :param is_terminal_activation: 如果是激活终端请求,则使用vendor的信息进行加密
        :param body: 如直接传入body,则不再进行序列化操作
        :param kwargs:
        :return:
        """
        if body is None:
            payload = {k: v for k, v in kwargs.items() if v not in (None, "")}
            body = json.dumps(payload)

        sn = self.vendor_sn if is_terminal_activation else self.terminal_sn
        key = self.vendor_key if is_terminal_activation else self.terminal_key
        assert all([sn, key])

        sign = md5_str(body + key)
        headers = {'Content-Type': 'application/json', 'Authorization': sn + " " + sign}
        return dict(data=body, headers=headers)

    def pay(self, total_amount, dynamic_id, subject=None, **kwargs):
        """
        付款
        :param client_sn: 商户系统订单号,必须在商户系统内唯一；且长度不超过64字节
        :param total_amount: 总金额,以分为单位
        :param dynamic_id: 条形内容
        :param subject: 交易简介
        :param wosai_store_id: terminal_sn与wosai_store_id不可同时为空
        :param payway: 1:支付宝 3:微信 4:百付宝 5:京东钱包
        :param operator: 门店操作员
        :param description: 商品详情
        :param longitude: 经度和纬度选填，但必须同时存在
        :param latitude:
        :param device_id: 设备标识
        :param extended: 扩展参数集合
        :param reflect: 反射参数,任何调用者希望原样返回的信息
        :return:
        """
        payload = dict(
            total_amount=str(total_amount),
            dynamic_id=str(dynamic_id),
            subject=subject or self._default_goods_subject,
            client_sn=kwargs.pop("client_sn", None) or str(int(time.time()*1000)) + gen_rand_str(4, 'digit'),
            terminal_sn=self.terminal_sn,
            device_id=self.device_id
        )
        payload.update(kwargs)
        req = self._make_signed_request_params(**payload)

        ret = self._call_api("/upay/v2/pay", req_kwargs=req)
        if ret['result_code'] == "200" and ret['biz_response']['data'].get('sn', None):
            self.last_order_sn = ret['biz_response']['data']['sn']
        return ret

    def refund(self, sn=None, refund_amount=1, client_sn=None, **kwargs):
        """
        退款
        :param refund_request_no: 商户退款所需序列号,表明是第几次退款
        :param sn: 收钱吧系统内部唯一订单号
        :param terminal_sn: 收钱吧终端ID
        :param client_sn: client_sn request_no 拼起来存到transaction里面的client_tsn
        :param refund_amount:
        :param operator:
        :param reflect
        :return:
        """
        if not any((sn, client_sn)):
            raise ValueError(u"必须传入sn或者client_sn的值")

        payload = dict(
            client_sn=client_sn,
            refund_request_no=kwargs.pop("refund_request_no", None) or gen_rand_str(4, 'digit'),
            sn=sn,
            refund_amount=str(refund_amount),
            terminal_sn=self.terminal_sn
        )
        payload.update(kwargs)

        req = self._make_signed_request_params(**payload)
        return self._call_api("/upay/v2/refund", req_kwargs=req)

    def query(self, sn=None, client_sn=None):
        """
        订单状态查询
        :param sn:
        :param client_sn:
        :return:
        """
        if not any((sn, client_sn)):
            raise ValueError(u"必须传入sn或者client_sn的值")
        payload = dict(
            sn=sn,
            client_sn=client_sn,
            terminal_sn=self.terminal_sn)
        return self._call_api("/upay/v2/query", req_kwargs=self._make_signed_request_params(**payload))

    def revoke(self, sn=None, client_sn=None):
        """
        用户手动撤单(退货)
        :param sn:
        :param client_sn:
        :return:
        """
        if not any((sn, client_sn)):
            raise ValueError(u"必须传入sn或者client_sn的值")
        payload = dict(
            sn=sn,
            client_sn=client_sn,
            terminal_sn=self.terminal_sn)
        return self._call_api("/upay/v2/revoke", req_kwargs=self._make_signed_request_params(**payload))

    def precreate(self, total_amount, payway="1", **kwargs):
        """
        扫二维码付款（C扫B）
        :param total_amount:
        :param payway:
        :param subject:
        :param client_sn:
        :param operator:
        :param description:
        :param longitude:
        :param latitude:
        :param device_id:
        :param extended:
        :param reflect:
        :return:
        """
        payload = dict(
            client_sn=kwargs.pop("client_sn", None) or str(int(time.time()*1000)) + gen_rand_str(4, 'digit'),
            subject=kwargs.pop('subject', None) or self._default_goods_subject,
            total_amount=str(total_amount),
            payway=str(payway),
            terminal_sn=self.terminal_sn,
        )
        payload.update(kwargs)
        req = self._make_signed_request_params(**payload)
        ret = self._call_api("/upay/v2/precreate", req_kwargs=req)
        if ret['result_code'] == "200" and ret['biz_response']['data'].get('sn', None):
            self.last_order_sn = ret['biz_response']['data']['sn']
        return ret

    def activate(self, code, override_terminal=False):
        """
        终端激活
        :param code:激活码
        :param device_id: 设备唯一身份ID
        :param os_info: 当前系统信息
        :param sdk_version: SDK版本
        :param type: 设备类型可以不提供.默认为2
        :param override_terminal: 是否覆盖当前client的terminal的配置,默认False
        :return:
        """
        payload = dict(
            code=code,
            device_id=self.device_id,
            sdk_version=self.sdk_version,
            os_info=self.os_info,
            type=self.device_type)
        req_params = self._make_signed_request_params(True, **payload)

        ret = self._call_api('/terminal/activate', req_kwargs=req_params)
        if override_terminal and ret['result_code'] == "200" and ret['biz_response'].get("terminal_sn") and \
                ret['biz_response'].get("terminal_key"):
            self.terminal_sn = ret['biz_response']['terminal_sn']
            self.terminal_key = ret['biz_response']['terminal_key']
        return ret

    def checkin(self):
        """
        终端签到
        :param terminal_sn: 终端号
        :param device_id: 设备唯一身份ID
        :param os_info: 当前系统信息
        :param sdk_version: SDK版本
        :return:
        """
        payload = dict(
            terminal_sn=self.terminal_sn,
            device_id=self.device_id,
            os_info=self.os_info,
            sdk_version=self.sdk_version
        )
        req_params = self._make_signed_request_params(**payload)

        ret = self._call_api('/terminal/checkin', req_kwargs=req_params)
        if ret['result_code'] == "200" and ret['biz_response'].get("terminal_sn") and \
                ret['biz_response'].get("terminal_key"):
            self.terminal_sn = ret['biz_response']['terminal_sn']
            self.terminal_key = ret['biz_response']['terminal_key']
        return ret

    def upload_log(self, body):
        """
        上传日志
        :param body: Body内容即为日志，请使用zip格式压缩
        :return:
        """
        req_params = self._make_signed_request_params(body=body)
        return self._call_api('/terminal/uploadLog', req_kwargs=req_params)
