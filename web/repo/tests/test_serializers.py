# Copyright 2022 by Open Kilt LLC. All rights reserved.
import datetime

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from repo.models import Package, PGPSigningKey, Repository


class SerializerValidationTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="admin_ser", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key
        self.signing_key = PGPSigningKey.objects.create(
            name="Test Key",
            email="test@example.com",
            fingerprint="FINGERPRINT12345",
            public_key_pem="dummy public",
            private_key_pem="dummy private",
        )

    def test_repo_uid_with_special_chars_rejected(self):
        """repo_uid with spaces or special chars is rejected"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "bad uid!", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("repo_uid", response.data)

    def test_repo_uid_disallowed_name_api_rejected(self):
        """repo_uid of 'api' is rejected as reserved"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "api", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("repo_uid", response.data)

    def test_repo_uid_disallowed_name_admin_rejected(self):
        """repo_uid of 'admin' is rejected as reserved"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "admin", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_repo_uid_disallowed_name_static_rejected(self):
        """repo_uid of 'static' is rejected as reserved"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "static", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_repo_without_signing_key_rejected(self):
        """Creating a repo without signing_key is rejected"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "valid-repo", "repo_type": "deb", "signing_key": ""},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_repo_uid_with_dash_and_underscore_accepted(self):
        """repo_uid with dash and underscore is valid"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "my_good-repo", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Repository.objects.filter(repo_uid="my_good-repo").count(), 1)

    def test_repo_uid_numeric_accepted(self):
        """repo_uid with numbers is valid"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "repo123", "repo_type": "rpm", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, 201)


class PackageSerializerTestCase(TestCase):
    def setUp(self):
        self.signing_key = PGPSigningKey.objects.create(
            name="Key",
            email="k@example.com",
            fingerprint="PKG_SER_FP",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(repo_uid="pkg-ser-repo", repo_type="deb", signing_key=self.signing_key)

    def test_package_relative_path(self):
        """Package.relative_path replaces dashes with slashes"""
        pkg = Package(
            repo=self.repo,
            package_uid="aa-bbccddee",
            filename="test.deb",
            package_name="test",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="abc",
        )
        self.assertEqual(pkg.relative_path(), "aa/bbccddee")

    def test_package_str_representation(self):
        """Package can be saved and retrieved"""
        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="zz-testpkg",
            filename="test.deb",
            package_name="testpkg",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="abc123",
        )
        self.assertEqual(Package.objects.filter(package_uid="zz-testpkg").count(), 1)
        self.assertEqual(pkg.relative_path(), "zz/testpkg")
