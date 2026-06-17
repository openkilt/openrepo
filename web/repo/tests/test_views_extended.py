# Copyright 2022 by Open Kilt LLC. All rights reserved.
import datetime
import os
import tempfile

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from repo.models import Package, PGPSigningKey, Repository


class CopyViewSetTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="copy_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="CopyKey",
            email="copy@example.com",
            fingerprint="COPY_FP_12345678",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo_deb = Repository.objects.create(
            repo_uid="copy-src-deb", repo_type="deb", signing_key=self.signing_key
        )
        self.repo_deb2 = Repository.objects.create(
            repo_uid="copy-dst-deb", repo_type="deb", signing_key=self.signing_key
        )
        self.repo_rpm = Repository.objects.create(
            repo_uid="copy-dst-rpm", repo_type="rpm", signing_key=self.signing_key
        )
        self.repo_files = Repository.objects.create(
            repo_uid="copy-dst-files", repo_type="files", signing_key=self.signing_key
        )
        self.pkg = Package.objects.create(
            repo=self.repo_deb,
            package_uid="copy-test-pkg",
            filename="hello.deb",
            package_name="hello",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="copy_hash",
        )

    def test_copy_deb_to_deb_succeeds(self):
        """Copying a deb package to another deb repo succeeds"""
        response = self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": self.repo_deb2.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Package.objects.filter(repo=self.repo_deb2, package_uid=self.pkg.package_uid).exists())

    def test_copy_deb_to_rpm_fails(self):
        """Copying a deb package to an rpm repo fails with 400"""
        response = self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": self.repo_rpm.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Incompatible destination repository", response.data["detail"])

    def test_copy_deb_to_generic_succeeds(self):
        """Copying any package to a generic 'files' repo succeeds"""
        response = self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": self.repo_files.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_copy_to_nonexistent_repo_fails(self):
        """Copying to a non-existent destination returns 404"""
        response = self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": "nonexistent-repo"},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_copy_duplicate_version_fails(self):
        """Copying a package that already exists in destination (same package_uid) fails"""
        # First copy succeeds
        self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": self.repo_deb2.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        # Copying the exact same package_uid again should fail (already exists)
        response = self.client.post(
            f"/api/{self.repo_deb.repo_uid}/pkg/{self.pkg.package_uid}/copy/",
            {"dest_repo_uid": self.repo_deb2.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class KeepOnlyLatestTestCase(APITestCase):
    """Test keep_only_latest flag behavior during upload and copy."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="latest_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="LatestKey",
            email="latest@example.com",
            fingerprint="LATEST_FP_1234",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.src_repo = Repository.objects.create(
            repo_uid="latest-src", repo_type="deb", signing_key=self.signing_key
        )
        self.dst_repo = Repository.objects.create(
            repo_uid="latest-dst",
            repo_type="deb",
            signing_key=self.signing_key,
            keep_only_latest=True,
        )

    def test_copy_with_keep_only_latest_removes_older(self):
        """When keep_only_latest=True, copying a newer version deletes older ones"""
        # Create an old package in dst
        old_pkg = Package.objects.create(
            repo=self.dst_repo,
            package_uid="latest-old-pkg",
            filename="myapp-0.9.deb",
            package_name="myapp",
            version="0.9",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="old_hash",
        )
        # Create a new package in src
        new_pkg = Package.objects.create(
            repo=self.src_repo,
            package_uid="latest-new-pkg",
            filename="myapp-1.0.deb",
            package_name="myapp",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="new_hash",
        )
        response = self.client.post(
            f"/api/{self.src_repo.repo_uid}/pkg/{new_pkg.package_uid}/copy/",
            {"dest_repo_uid": self.dst_repo.repo_uid},
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Old package should be gone
        self.assertFalse(Package.objects.filter(pk=old_pkg.pk).exists())
        # New package should exist
        self.assertTrue(Package.objects.filter(repo=self.dst_repo, package_name="myapp", version="1.0").exists())


class RepoDetailApiTestCase(APITestCase):
    """Test repo detail endpoint."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="detail_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="DetailKey",
            email="detail@example.com",
            fingerprint="DETAIL_FP_1234",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="detail-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )

    def test_get_repo_detail(self):
        """GET /api/<repo>/ returns repo details"""
        response = self.client.get(f"/api/{self.repo.repo_uid}/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["repo_uid"], self.repo.repo_uid)
        self.assertIn("repo_instructions", response.data)
        self.assertIn("signing_key", response.data)

    def test_repo_instructions_contain_apt_update(self):
        """repo_instructions for deb type contain apt commands"""
        response = self.client.get(f"/api/{self.repo.repo_uid}/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertIn("apt update", response.data["repo_instructions"])

    def test_list_repos(self):
        """GET /api/repos/ returns a list"""
        response = self.client.get("/api/repos/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_update_signing_key_marks_stale(self):
        """Updating a repo's signing key marks it as stale"""
        new_key = PGPSigningKey.objects.create(
            name="New Key",
            email="new@example.com",
            fingerprint="NEW_FP_5678",
            public_key_pem="pub2",
            private_key_pem="priv2",
        )
        response = self.client.put(
            f"/api/{self.repo.repo_uid}/",
            {
                "repo_uid": self.repo.repo_uid,
                "repo_type": self.repo.repo_type,
                "signing_key": new_key.fingerprint,
                "keep_only_latest": False,
            },
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.repo.refresh_from_db()
        self.assertTrue(self.repo.is_stale)


class BuildApiTestCase(APITestCase):
    """Test build and build log API endpoints."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="build_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="BuildKey",
            email="build@example.com",
            fingerprint="BUILD_FP_1234",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="build-test-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )
        from repo.models import Build, BuildLogLine

        self.build = Build.objects.create(
            repo=self.repo,
            build_number=1,
            completion_status=Build.STATUS_COMPLETE_SUCCESS,
        )
        self.log_line = BuildLogLine.objects.create(
            build=self.build,
            command="createrepo",
            message="OK",
            loglevel="info",
            line_number=0,
            execution_time_sec=1.5,
            exec_complete=True,
        )

    def test_list_builds(self):
        """GET /api/builds/ returns a list"""
        response = self.client.get("/api/builds/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["build_number"], 1)

    def test_list_build_logs(self):
        """GET /api/buildlogs/ returns a list"""
        response = self.client.get("/api/buildlogs/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["command"], "createrepo")


class OverwriteUploadTestCase(APITestCase):
    """Test the overwrite=true/false behavior during package upload."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="ow_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = self.test_dir

        self.signing_key = PGPSigningKey.objects.create(
            name="OWKey",
            email="ow@example.com",
            fingerprint="OW_FP_12345678",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(repo_uid="ow-repo", repo_type="deb", signing_key=self.signing_key)

    def _upload_deb(self, overwrite="0"):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, "unittest_files/hello-world_1.0.0_all.deb")
        with open(deb_path, "rb") as f:
            response = self.client.post(
                f"/api/{self.repo.repo_uid}/upload/",
                data={"package_file": f, "overwrite": overwrite},
                format="multipart",
                HTTP_AUTHORIZATION=f"Token {self.admin_token}",
            )
        return response

    def test_upload_duplicate_without_overwrite_fails(self):
        """Uploading the same package twice without overwrite fails"""
        self._upload_deb()
        response = self._upload_deb()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", response.data["detail"])

    def test_upload_duplicate_with_overwrite_succeeds(self):
        """Uploading the same package twice with overwrite=true replaces it"""
        self._upload_deb()
        response = self._upload_deb(overwrite="true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still only have one package
        self.assertEqual(Package.objects.filter(repo=self.repo, package_name="hello-world").count(), 1)

    def test_upload_overwrite_yes_string(self):
        """overwrite='yes' is treated as True"""
        self._upload_deb()
        response = self._upload_deb(overwrite="yes")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PGPKeyApiTestCase(APITestCase):
    """Test PGP key management API."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="pgp_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="PGPKey",
            email="pgp@example.com",
            fingerprint="PGP_FP_12345678",
            public_key_pem="pub",
            private_key_pem="priv",
        )

    def test_list_signing_keys(self):
        """GET /api/signingkeys/ returns the keys"""
        response = self.client.get("/api/signingkeys/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_delete_signing_key_referenced_by_repo_fails(self):
        """Deleting a signing key used by a repo returns 400"""
        Repository.objects.create(
            repo_uid="pgp-ref-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )
        response = self.client.delete(
            f"/api/signingkeys/{self.signing_key.fingerprint}/",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to delete", response.data["detail"])
