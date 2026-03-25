#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.dependencies import TokenProvider


class TestTokenProvider(unittest.TestCase):
    def test_refresh_when_expired(self):
        provider = TokenProvider()
        provider._token = "old"
        provider._expires_at = time.time() - 1

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": "new", "expires_in": 3600}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            token = provider.get_token()

        self.assertEqual(token, "new")
        self.assertTrue(provider._expires_at and provider._expires_at > time.time())
        mock_post.assert_called_once()

    def test_no_refresh_when_valid(self):
        provider = TokenProvider()
        provider._token = "cached"
        provider._expires_at = time.time() + 3600

        with patch("requests.post") as mock_post:
            token = provider.get_token()

        self.assertEqual(token, "cached")
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()

