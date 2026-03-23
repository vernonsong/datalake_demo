#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mock服务兼容入口"""

import sys

from mock_service.api_server import run_api_server


def run_server(port=5001):
    """运行Mock服务"""
    run_api_server(port)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    run_server(port)
