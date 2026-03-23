#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mock_server兼容入口测试
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mock_service.mock_server import run_server


class TestMockServerEntry(unittest.TestCase):
    """测试mock_server兼容入口"""

    def test_run_server_delegate_to_api_server(self):
        """测试run_server委托给api_server"""
        with patch("mock_service.mock_server.run_api_server") as mock_run:
            run_server(5003)
        mock_run.assert_called_once_with(5003)


if __name__ == "__main__":
    unittest.main()
