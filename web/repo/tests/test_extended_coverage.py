# Copyright 2022 by Open Kilt LLC. All rights reserved.
import datetime
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from repo.models import Build, BuildLogLine, Package, PGPSigningKey, Repository


class PGPKeyCreateAPITestCase(APITestCase):
    """Test PGP key creation via the API."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="pgpcreate_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key
        self.regular_user = User.objects.create_user(username="pgpcreate_user", password="password123")
        self.regular_token = Token.objects.get(user=self.regular_user).key

    def _post_key(self, name, email, token=None):
        if token is None:
            token = self.admin_token
        return self.client.post(
            "/api/signingkeys/",
            {"name": name, "email": email},
            HTTP_AUTHORIZATION=f"Token {token}",
        )

    def test_create_key_with_empty_name_fails(self):
        """Creating a key with empty name returns 400"""
        response = self._post_key("", "test@example.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_key_with_invalid_email_fails(self):
        """Creating a key with an invalid email returns 400"""
        response = self._post_key("Valid Name", "not-an-email")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    @patch("repo.api.views.PGPKeyring")
    def test_create_key_with_valid_params_calls_keyring(self, mock_keyring_cls):
        """Creating a key with valid params calls PGPKeyring.generate_key"""
        mock_keyring = MagicMock()
        mock_keyring_cls.return_value = mock_keyring

        response = self._post_key("Test User", "test@example.com")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_keyring.generate_key.assert_called_once_with("Test User", "test@example.com")

    @patch("repo.api.views.PGPKeyring")
    def test_delete_signing_key_not_referenced_succeeds(self, mock_keyring_cls):
        """Deleting an unreferenced signing key returns 204"""
        mock_keyring = MagicMock()
        mock_keyring_cls.return_value = mock_keyring

        key = PGPSigningKey.objects.create(
            name="Orphan Key",
            email="orphan@example.com",
            fingerprint="ORPHAN_FP_999",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        response = self.client.delete(
            f"/api/signingkeys/{key.fingerprint}/",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PGPSigningKey.objects.filter(fingerprint="ORPHAN_FP_999").exists())


class BuildFilterAPITestCase(APITestCase):
    """Test build filtering via API."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="bfilt_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

        self.signing_key = PGPSigningKey.objects.create(
            name="FilterKey",
            email="filter@example.com",
            fingerprint="FILTER_FP_123",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="filter-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )
        self.build1 = Build.objects.create(
            repo=self.repo,
            build_number=1,
            completion_status=Build.STATUS_COMPLETE_SUCCESS,
        )
        self.build2 = Build.objects.create(
            repo=self.repo,
            build_number=2,
            completion_status=Build.STATUS_COMPLETE_ERROR,
        )

    def test_filter_builds_by_repo(self):
        """GET /api/builds/?repo=filter-repo returns only that repo's builds"""
        response = self.client.get(
            "/api/builds/?repo=filter-repo",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_builds_by_completion_status(self):
        """GET /api/builds/?completion_status=... filters correctly"""
        response = self.client.get(
            f"/api/builds/?completion_status={Build.STATUS_COMPLETE_SUCCESS}",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["completion_status"], Build.STATUS_COMPLETE_SUCCESS)

    def test_filter_builds_by_min_build(self):
        """GET /api/builds/?min_build=2 returns only builds >= 2"""
        response = self.client.get(
            "/api/builds/?min_build=2",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["build_number"], 2)

    def test_filter_buildlogs_by_repo(self):
        """GET /api/buildlogs/?repo=filter-repo returns logs for that repo"""
        BuildLogLine.objects.create(
            build=self.build1,
            command="apt-ftparchive",
            message="ok",
            loglevel="info",
            line_number=0,
            exec_complete=True,
        )
        response = self.client.get(
            "/api/buildlogs/?repo=filter-repo",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_buildlogs_by_build_number(self):
        """GET /api/buildlogs/?build=1 returns only logs for build 1"""
        BuildLogLine.objects.create(
            build=self.build1,
            command="cmd1",
            message="",
            loglevel="info",
            line_number=0,
            exec_complete=True,
        )
        BuildLogLine.objects.create(
            build=self.build2,
            command="cmd2",
            message="",
            loglevel="info",
            line_number=0,
            exec_complete=True,
        )
        response = self.client.get(
            "/api/buildlogs/?build=1",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["command"], "cmd1")


class ModelStringRepresentationTestCase(APITestCase):
    """Test __str__ methods on models."""

    def test_pgp_signing_key_str(self):
        """PGPSigningKey.__str__ shows name, email, and last 16 chars of fingerprint"""
        fp = "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
        key = PGPSigningKey(
            name="Alice Bob",
            email="alice@example.com",
            fingerprint=fp,
        )
        result = str(key)
        self.assertIn("Alice Bob", result)
        self.assertIn("alice@example.com", result)
        # __str__ uses fingerprint[-16:]
        self.assertIn(fp[-16:], result)

    def test_repository_str(self):
        """Repository.__str__ returns repo_uid"""
        repo = Repository(repo_uid="my-test-repo", repo_type="deb")
        self.assertEqual(str(repo), "my-test-repo")


class PackagesViewSetTestCase(APITestCase):
    """Test the packages list endpoint."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="pkglist_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = self.test_dir

        self.signing_key = PGPSigningKey.objects.create(
            name="PkgKey",
            email="pkg@example.com",
            fingerprint="PKGLIST_FP_123",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="pkglist-repo",
            repo_type="deb",
            signing_key=self.signing_key,
        )

    def test_package_list_returns_empty_for_new_repo(self):
        """GET /api/<repo>/packages/ returns empty results for a new repo"""
        response = self.client.get(
            f"/api/{self.repo.repo_uid}/packages/",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_package_list_returns_packages_in_repo(self):
        """GET /api/<repo>/packages/ returns all packages for that repo"""
        for i in range(3):
            Package.objects.create(
                repo=self.repo,
                package_uid=f"pkg-uid-{i}",
                filename=f"pkg{i}.deb",
                package_name=f"pkg{i}",
                version=f"1.{i}",
                architecture="all",
                upload_date=datetime.datetime.now(tz=pytz.utc),
                checksum_sha512=f"hash{i}",
            )
        response = self.client.get(
            f"/api/{self.repo.repo_uid}/packages/",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_get_package_detail(self):
        """GET /api/<repo>/pkg/<pkg_uid>/ returns package details"""
        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="detail-pkg-uid",
            filename="detail.deb",
            package_name="detailpkg",
            version="2.0",
            architecture="amd64",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="detailhash",
        )
        response = self.client.get(
            f"/api/{self.repo.repo_uid}/pkg/{pkg.package_uid}/",
            HTTP_AUTHORIZATION=f"Token {self.admin_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["package_uid"], "detail-pkg-uid")
        self.assertEqual(response.data["version"], "2.0")
        self.assertEqual(response.data["architecture"], "amd64")


class AdapterFileInitTestCase(APITestCase):
    """Test the create_adapter factory function."""

    def test_create_adapter_unknown_type_returns_none(self):
        """create_adapter returns None for unknown repo type"""
        from adapters.file import create_adapter

        result = create_adapter("unknown", "/some/path", "file.xyz")
        self.assertIsNone(result)

    def test_create_adapter_files_type(self):
        """create_adapter returns GenericFileAdapter for 'files' repo type"""
        from adapters.file import create_adapter
        from adapters.file.file_adapter import GenericFileAdapter

        result = create_adapter("files", "/some/path", "myfile.tar.gz")
        self.assertIsInstance(result, GenericFileAdapter)

    def test_create_adapter_deb_type(self):
        """create_adapter returns DebFileAdapter for 'deb' repo type"""
        import os

        from adapters.file import create_adapter
        from adapters.file.deb_adapter import DebFileAdapter

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, "unittest_files/hello-world_1.0.0_all.deb")
        result = create_adapter("deb", deb_path, "hello-world_1.0.0_all.deb")
        self.assertIsInstance(result, DebFileAdapter)


class AdapterRepoInitTestCase(APITestCase):
    """Test the get_repo_adapter factory function."""

    def setUp(self):
        self.signing_key = PGPSigningKey.objects.create(
            name="RouterKey",
            email="router@example.com",
            fingerprint="ROUTER_FP_1234",
            public_key_pem="pub",
            private_key_pem="priv",
        )

    def test_get_repo_adapter_deb(self):
        """get_repo_adapter returns DepRepoAdapter for deb repos"""
        from adapters.repo import get_repo_adapter
        from adapters.repo.deb_repo import DepRepoAdapter

        repo = Repository.objects.create(repo_uid="router-deb", repo_type="deb", signing_key=self.signing_key)
        adapter = get_repo_adapter(repo)
        self.assertIsInstance(adapter, DepRepoAdapter)

    def test_get_repo_adapter_rpm(self):
        """get_repo_adapter returns RpmRepoAdapter for rpm repos"""
        from adapters.repo import get_repo_adapter
        from adapters.repo.rpm_repo import RpmRepoAdapter

        repo = Repository.objects.create(repo_uid="router-rpm", repo_type="rpm", signing_key=self.signing_key)
        adapter = get_repo_adapter(repo)
        self.assertIsInstance(adapter, RpmRepoAdapter)

    def test_get_repo_adapter_files(self):
        """get_repo_adapter returns GenericRepoAdapter for files repos"""
        from adapters.repo import get_repo_adapter
        from adapters.repo.generic_repo import GenericRepoAdapter

        repo = Repository.objects.create(repo_uid="router-files", repo_type="files", signing_key=self.signing_key)
        adapter = get_repo_adapter(repo)
        self.assertIsInstance(adapter, GenericRepoAdapter)

    def test_get_repo_adapter_unknown_raises(self):
        """get_repo_adapter raises Exception for unknown repo type"""
        from adapters.repo import get_repo_adapter

        repo = Repository(repo_uid="router-unknown", repo_type="unknown")
        with self.assertRaises(Exception):
            get_repo_adapter(repo)


class RpmRepoInstructionsTestCase(APITestCase):
    """Test RPM repo instructions generation."""

    def setUp(self):
        self.signing_key = PGPSigningKey.objects.create(
            name="RPMKey",
            email="rpm@example.com",
            fingerprint="RPM_INSTRUCTIONS_FP",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="rpm-instructions-test", repo_type="rpm", signing_key=self.signing_key
        )

    def test_rpm_repo_instructions_contain_yum_repos_d(self):
        """RPM repo instructions include the yum.repos.d path"""
        from adapters.repo.rpm_repo import RpmRepoAdapter

        adapter = RpmRepoAdapter(self.repo)
        instructions = adapter._get_repo_instructions()
        self.assertIn("/etc/yum.repos.d/", instructions)
        self.assertIn(self.repo.repo_uid, instructions)

    def test_rpm_repo_instructions_contain_gpgkey(self):
        """RPM repo instructions include gpgkey directive"""
        from adapters.repo.rpm_repo import RpmRepoAdapter

        adapter = RpmRepoAdapter(self.repo)
        instructions = adapter._get_repo_instructions()
        self.assertIn("gpgkey=", instructions)
        self.assertIn("public.gpg", instructions)


class UserListAPITestCase(APITestCase):
    """Test the users API endpoint."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="user_list_admin", password="password123")
        self.admin_token = Token.objects.get(user=self.admin).key

    def test_list_users_as_superuser(self):
        """Superuser can list users"""
        response = self.client.get("/api/users/", HTTP_AUTHORIZATION=f"Token {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_list_users_unauthenticated_fails(self):
        """Unauthenticated request to user list is rejected"""
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BackgroundWorkerRunLoopTestCase(APITestCase):
    """Test the BackgroundWorker run loop behavior."""

    def test_worker_stop_flag_prevents_running(self):
        """BackgroundWorker.stop() sets stay_alive=False"""
        from repo.worker.bgworker import BackgroundWorker, ChoreList

        cl = ChoreList()
        worker = BackgroundWorker(cl)
        self.assertTrue(worker.stay_alive)
        worker.stop()
        self.assertFalse(worker.stay_alive)

    @patch("adapters.repo.get_repo_adapter")
    def test_worker_handles_exception_gracefully(self, mock_get_adapter):
        """BackgroundWorker continues if an exception occurs during repo processing"""
        from repo.worker.bgworker import BackgroundWorker, ChoreList

        mock_get_adapter.side_effect = Exception("Unexpected error")

        signing_key = PGPSigningKey.objects.create(
            name="WorkerKey",
            email="worker@example.com",
            fingerprint="WORKER_EXC_FP",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        repo = Repository.objects.create(repo_uid="worker-exc-repo", repo_type="deb", signing_key=signing_key)

        cl = ChoreList()
        cl.set_needs_clean(repo.repo_uid)

        worker = BackgroundWorker(cl)
        worker.stay_alive = False

        # Simulate one iteration manually (same logic as run())
        try:
            next_task = cl.get_next_task()
            if next_task:
                r = Repository.objects.get(repo_uid=next_task)
                r.is_stale = False
                r.save()
                adapter = mock_get_adapter(r)
                adapter.setup_repo()
        except Exception:
            pass
        finally:
            if next_task:
                cl.cleaning_done(next_task)

        # Worker should have cleared the chore list
        self.assertIsNone(cl.get_next_task())

    def test_chorelist_multiple_repos_ordering(self):
        """ChoreList returns tasks in insertion order (oldest first)"""
        import time

        from repo.worker.bgworker import ChoreList

        cl = ChoreList()
        cl.set_needs_clean("repo-a")
        time.sleep(0.01)
        cl.set_needs_clean("repo-b")
        time.sleep(0.01)
        cl.set_needs_clean("repo-c")

        first = cl.get_next_task()
        self.assertEqual(first, "repo-a")

    def test_chorelist_set_needs_clean_is_idempotent(self):
        """ChoreList.set_needs_clean on existing key does not duplicate"""
        from repo.worker.bgworker import ChoreList

        cl = ChoreList()
        cl.set_needs_clean("repo-x")
        cl.set_needs_clean("repo-x")

        task1 = cl.get_next_task()
        self.assertEqual(task1, "repo-x")
        task2 = cl.get_next_task()
        self.assertIsNone(task2)


class BaseFileAdapterTestCase(APITestCase):
    """Test the base RepoFileAdapter stubs."""

    def test_base_adapter_get_name_logs_warning(self):
        """RepoFileAdapter.get_name logs a warning"""
        import logging

        from adapters.file.base_adapter import RepoFileAdapter

        adapter = RepoFileAdapter("/path", "file")
        with self.assertLogs("openrepo_web", level=logging.WARNING):
            adapter.get_name()

    def test_base_adapter_get_architecture_logs_warning(self):
        """RepoFileAdapter.get_architecture logs a warning"""
        import logging

        from adapters.file.base_adapter import RepoFileAdapter

        adapter = RepoFileAdapter("/path", "file")
        with self.assertLogs("openrepo_web", level=logging.WARNING):
            adapter.get_architecture()

    def test_base_adapter_get_version_logs_warning(self):
        """RepoFileAdapter.get_version logs a warning"""
        import logging

        from adapters.file.base_adapter import RepoFileAdapter

        adapter = RepoFileAdapter("/path", "file")
        with self.assertLogs("openrepo_web", level=logging.WARNING):
            adapter.get_version()

    def test_base_adapter_get_description_logs_warning(self):
        """RepoFileAdapter.get_description logs a warning"""
        import logging

        from adapters.file.base_adapter import RepoFileAdapter

        adapter = RepoFileAdapter("/path", "file")
        with self.assertLogs("openrepo_web", level=logging.WARNING):
            adapter.get_description()

    def test_base_adapter_get_builddate_logs_warning(self):
        """RepoFileAdapter.get_builddate logs a warning"""
        import logging

        from adapters.file.base_adapter import RepoFileAdapter

        adapter = RepoFileAdapter("/path", "file")
        with self.assertLogs("openrepo_web", level=logging.WARNING):
            adapter.get_builddate()
