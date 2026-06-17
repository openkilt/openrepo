# Copyright 2022 by Open Kilt LLC. All rights reserved.
import hashlib
import os
import tempfile

from django.test import TestCase

from repo.api.util import compute_sha512, reduce_to_uid


class UtilTestCase(TestCase):
    def test_reduce_to_uid_basic(self):
        """reduce_to_uid lowercases and slugifies a string"""
        result = reduce_to_uid("My Repo Name")
        self.assertEqual(result, "my-repo-name")

    def test_reduce_to_uid_special_chars(self):
        """reduce_to_uid strips special characters"""
        result = reduce_to_uid("Hello World! @#$%")
        self.assertEqual(result, "hello-world")

    def test_reduce_to_uid_already_clean(self):
        """reduce_to_uid passes through clean slugs unchanged"""
        result = reduce_to_uid("my-repo-123")
        self.assertEqual(result, "my-repo-123")

    def test_reduce_to_uid_empty_string(self):
        """reduce_to_uid on empty string returns empty"""
        result = reduce_to_uid("")
        self.assertEqual(result, "")

    def test_compute_sha512_known_value(self):
        """compute_sha512 returns correct hex digest"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"hello world")
            tmp_path = tmp.name
        try:
            result = compute_sha512(tmp_path)
            expected = hashlib.sha512(b"hello world").hexdigest()
            self.assertEqual(result, expected)
        finally:
            os.unlink(tmp_path)

    def test_compute_sha512_empty_file(self):
        """compute_sha512 of empty file matches sha512 of empty string"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = compute_sha512(tmp_path)
            expected = hashlib.sha512(b"").hexdigest()
            self.assertEqual(result, expected)
        finally:
            os.unlink(tmp_path)

    def test_compute_sha512_large_file(self):
        """compute_sha512 works on multi-chunk files (> 64KB)"""
        data = b"x" * (1024 * 128)  # 128 KB
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            result = compute_sha512(tmp_path)
            expected = hashlib.sha512(data).hexdigest()
            self.assertEqual(result, expected)
        finally:
            os.unlink(tmp_path)

    def test_compute_sha512_returns_hex_string(self):
        """compute_sha512 returns a 128-char hex string"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name
        try:
            result = compute_sha512(tmp_path)
            self.assertEqual(len(result), 128)
            int(result, 16)  # should not raise
        finally:
            os.unlink(tmp_path)
