# -*- coding: utf-8 -*-

import logging
import logging.config
from pythonjsonlogger import jsonlogger

try:
    import simplejson as json
except (ImportError, SyntaxError):
    import json

simple_fmt = "%(asctime)s - %(levelname)s- %(name)s - %(funcName)s: %(message)s"
thread_fmt = "%(asctime)s - %(levelname)s- %(name)s - %(funcName)s - %(threadName)s: %(message)s"

json_formatter = jsonlogger.JsonFormatter(thread_fmt, json_encoder=json.JSONEncoder)
simple_formatter = logging.Formatter(simple_fmt)
thread_formatter = logging.Formatter(thread_fmt)

json_console_handler = logging.StreamHandler()
json_console_handler.setFormatter(json_formatter)
json_console_handler.setLevel(logging.INFO)

# 日志默认配置
logging.config.dictConfig({"disable_existing_loggers": False, "version": 1})
logging.root.handlers = [json_console_handler]  # 默认会添加一个默认的handler,需要移除
logging.root.setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.WARN)
