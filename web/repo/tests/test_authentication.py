# Copyright 2022 by Open Kilt LLC. All rights reserved.
import datetime

import pytz
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from repo.models import Package, PGPSigningKey, Repository


class AuthPermissionTestCase(APITestCase):
    """Test the CustomOpenRepoPermission class through the full API."""

    def setUp(self):
        User = get_user_model()
        self.regular_user = User.objects.create_user(username="regularuser", password="password123")
        self.super_user = User.objects.create_superuser(username="superuser", password="password123")
        self.other_user = User.objects.create_user(username="otheruser", password="password123")

        self.regular_token = Token.objects.get(user=self.regular_user).key
        self.super_token = Token.objects.get(user=self.super_user).key
        self.other_token = Token.objects.get(user=self.other_user).key

        self.signing_key = PGPSigningKey.objects.create(
            name="AuthKey",
            email="auth@example.com",
            fingerprint="AUTH_FP_12345678",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="auth-test-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )
        # Grant regular_user write access to this repo
        self.repo.write_access.add(self.regular_user)

    def test_unauthenticated_read_rejected(self):
        """Unauthenticated requests are rejected even for safe methods"""
        response = self.client.get("/api/repos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_read_allowed(self):
        """Authenticated regular user can read repos list"""
        response = self.client.get("/api/repos/", HTTP_AUTHORIZATION=f"Token {self.regular_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_repo(self):
        """Regular user (not superuser) cannot create a new repo"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "new-repo", "repo_type": "deb", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.regular_token}",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_create_repo(self):
        """Superuser can create a new repo"""
        response = self.client.post(
            "/api/repos/",
            {"repo_uid": "superuser-repo", "repo_type": "rpm", "signing_key": self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f"Token {self.super_token}",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_delete_repo_without_access(self):
        """Regular user without write access cannot delete a repo"""
        response = self.client.delete(
            f"/api/{self.repo.repo_uid}/",
            HTTP_AUTHORIZATION=f"Token {self.other_token}",
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_superuser_can_delete_repo(self):
        """Superuser can delete any repo"""
        repo_to_delete = Repository.objects.create(
            repo_uid="delete-me", repo_type="files", signing_key=self.signing_key
        )
        response = self.client.delete(
            f"/api/{repo_to_delete.repo_uid}/",
            HTTP_AUTHORIZATION=f"Token {self.super_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Repository.objects.filter(repo_uid="delete-me").exists())

    def test_superuser_can_read_packages(self):
        """Superuser can list packages for a repo"""
        response = self.client.get(
            f"/api/{self.repo.repo_uid}/packages/",
            HTTP_AUTHORIZATION=f"Token {self.super_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_can_read_packages(self):
        """Regular user can list packages (safe method)"""
        response = self.client.get(
            f"/api/{self.repo.repo_uid}/packages/",
            HTTP_AUTHORIZATION=f"Token {self.regular_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_without_write_access_cannot_delete_package(self):
        """User without repo write access cannot delete a package"""
        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="auth-test-pkg",
            filename="test.deb",
            package_name="test",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="auth_hash",
        )
        response = self.client.delete(
            f"/api/{self.repo.repo_uid}/pkg/{pkg.package_uid}/",
            HTTP_AUTHORIZATION=f"Token {self.other_token}",
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_with_write_access_can_delete_package(self):
        """User with repo write access can delete a package"""
        import os
        import tempfile

        from django.conf import settings

        settings.STORAGE_PATH = tempfile.mkdtemp()
        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="auth-del-pkg",
            filename="test.deb",
            package_name="test",
            version="2.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="auth_hash_2",
        )
        # Create a dummy file so deletion signal doesn't fail
        pkg_path = os.path.join(settings.STORAGE_PATH, pkg.relative_path())
        os.makedirs(os.path.dirname(pkg_path), exist_ok=True)
        with open(pkg_path, "w") as f:
            f.write("dummy")

        response = self.client.delete(
            f"/api/{self.repo.repo_uid}/pkg/{pkg.package_uid}/",
            HTTP_AUTHORIZATION=f"Token {self.regular_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_whoami_endpoint(self):
        """whoami returns correct user info"""
        response = self.client.get("/api/whoami", HTTP_AUTHORIZATION=f"Token {self.regular_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "regularuser")
        self.assertFalse(response.data["is_superuser"])
