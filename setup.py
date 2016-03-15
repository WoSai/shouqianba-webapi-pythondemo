# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os

setup(
    name='shouqianba',
    version=open('version', 'r').read().strip(),
    packages=['shouqianba'],
    url='https://github.com/WoSai/shouqianba-webapi-pythondemo',
    license='MIT',
    author='Xu Hao',
    author_email='xuhao@wosai-inc.com',
    description='Shouqianba SDK for Python',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
    ],
    long_description=open(
        os.path.join(os.path.dirname(__file__), "README.md"), 'r').read(),
    install_requires=[
        "requests",
        "simplejson",
        "python-json-logger"
    ]
)