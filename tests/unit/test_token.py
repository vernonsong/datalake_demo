#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token服务单元测试
"""

import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_service.token_service import TokenService


class TestTokenServiceInit(unittest.TestCase):
    """测试TokenService初始化"""

    def test_init_with_default(self):
        """测试默认初始化"""
        service = TokenService()
        self.assertEqual(service.secret, "jwt-secret-key-for-token-generation")
        self.assertEqual(service.expires_in, 3600)

    def test_init_with_custom_params(self):
        """测试自定义参数初始化"""
        service = TokenService(secret="custom-secret", expires_in=7200)
        self.assertEqual(service.secret, "custom-secret")
        self.assertEqual(service.expires_in, 7200)


class TestTokenGenerate(unittest.TestCase):
    """测试Token生成"""

    def test_generate_token_basic(self):
        """测试生成基础Token"""
        service = TokenService(secret="test-secret")
        token = service.generate_token()
        self.assertIsInstance(token, str)
        parts = token.split(".")
        self.assertGreaterEqual(len(parts), 3)

    def test_generate_token_with_payload(self):
        """测试生成带载荷的Token"""
        service = TokenService(secret="test-secret")
        payload = {"user_id": 123, "role": "admin"}
        token = service.generate_token(payload)
        self.assertIsInstance(token, str)

    def test_generate_token_consistency(self):
        """测试Token生成一致性（同时间戳token相同）"""
        service = TokenService(secret="test-secret")
        token1 = service.generate_token()
        token2 = service.generate_token()
        self.assertEqual(token1, token2)


class TestTokenVerify(unittest.TestCase):
    """测试Token验证"""

    def test_verify_valid_token(self):
        """测试验证有效Token"""
        service = TokenService(secret="test-secret")
        token = service.generate_token()
        self.assertTrue(service.verify_token(token))

    def test_verify_invalid_token(self):
        """测试验证无效Token"""
        service = TokenService(secret="test-secret")
        self.assertFalse(service.verify_token("invalid-token"))
        self.assertFalse(service.verify_token(""))
        self.assertFalse(service.verify_token("a.b.c"))

    def test_verify_wrong_secret(self):
        """测试密钥不匹配"""
        service1 = TokenService(secret="secret1")
        service2 = TokenService(secret="secret2")
        token = service1.generate_token()
        self.assertFalse(service2.verify_token(token))

    def test_verify_tampered_token(self):
        """测试篡改的Token"""
        service = TokenService(secret="test-secret")
        token = service.generate_token()
        tampered_token = token[:-5] + "xxxxx"
        self.assertFalse(service.verify_token(tampered_token))


class TestTokenExpiration(unittest.TestCase):
    """测试Token过期"""

    def test_verify_expired_token(self):
        """测试过期Token"""
        service = TokenService(secret="test-secret", expires_in=-1)
        token = service.generate_token()
        time.sleep(0.1)
        self.assertFalse(service.verify_token(token))

    def test_verify_valid_after_short_time(self):
        """测试短时间后Token仍有效"""
        service = TokenService(secret="test-secret", expires_in=1)
        token = service.generate_token()
        time.sleep(0.1)
        self.assertTrue(service.verify_token(token))


class TestTokenPayload(unittest.TestCase):
    """测试Token载荷"""

    def test_verify_token_with_payload(self):
        """测试验证带载荷的Token"""
        service = TokenService(secret="test-secret")
        payload = {"user_id": 123, "name": "test"}
        token = service.generate_token(payload)
        is_valid, extracted_payload = service.verify_token_with_payload(token)
        self.assertTrue(is_valid)
        self.assertEqual(extracted_payload.get("user_id"), 123)
        self.assertEqual(extracted_payload.get("name"), "test")

    def test_verify_token_with_empty_payload(self):
        """测试无载荷的Token"""
        service = TokenService(secret="test-secret")
        token = service.generate_token()
        is_valid, extracted_payload = service.verify_token_with_payload(token)
        self.assertTrue(is_valid)
        self.assertEqual(extracted_payload, {})


class TestTokenTimestamp(unittest.TestCase):
    """测试Token时间戳"""

    def test_extract_timestamp(self):
        """测试提取时间戳"""
        service = TokenService(secret="test-secret")
        token = service.generate_token()
        ts = service.extract_timestamp(token)
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)

    def test_extract_timestamp_invalid(self):
        """测试提取无效Token的时间戳"""
        service = TokenService(secret="test-secret")
        ts = service.extract_timestamp("invalid")
        self.assertEqual(ts, 0)


class TestTokenSecurity(unittest.TestCase):
    """测试Token安全性"""

    def test_token_contains_signature(self):
        """测试Token包含签名"""
        service = TokenService(secret="test-secret")
        token = service.generate_token({"data": "test"})
        parts = token.split(".")
        signature = parts[3]
        self.assertGreater(len(signature), 0)

    def test_different_payloads_different_tokens(self):
        """测试不同载荷生成不同Token"""
        service = TokenService(secret="test-secret")
        token1 = service.generate_token({"user": "alice"})
        token2 = service.generate_token({"user": "bob"})
        self.assertNotEqual(token1, token2)


class TestTokenEdgeCases(unittest.TestCase):
    """边界测试"""

    def test_verify_none_token(self):
        """测试None Token"""
        service = TokenService(secret="test-secret")
        self.assertFalse(service.verify_token(None))

    def test_verify_dict_token(self):
        """测试字典类型Token"""
        service = TokenService(secret="test-secret")
        self.assertFalse(service.verify_token({"token": "value"}))

    def test_generate_token_with_none_payload(self):
        """测试None载荷"""
        service = TokenService(secret="test-secret")
        token = service.generate_token(None)
        self.assertIsInstance(token, str)

    def test_verify_with_payload_invalid_token(self):
        """测试无效Token的载荷提取"""
        service = TokenService(secret="test-secret")
        is_valid, payload = service.verify_token_with_payload("invalid")
        self.assertFalse(is_valid)
        self.assertEqual(payload, {})


if __name__ == "__main__":
    unittest.main()
