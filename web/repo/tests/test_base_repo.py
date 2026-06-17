# Copyright 2022 by Open Kilt LLC. All rights reserved.
import datetime
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytz
from django.conf import settings
from django.test import TestCase

from adapters.repo.base_repo import BaseRepoAdapter
from adapters.repo.generic_repo import GenericRepoAdapter
from repo.models import Build, BuildLogLine, Package, PGPSigningKey, Repository


class BaseRepoAdapterBuildLogTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = os.path.join(self.test_dir, "storage")
        settings.REPO_WWW_PATH = os.path.join(self.test_dir, "www")
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        settings.DEB_DB_PATH = os.path.join(self.test_dir, "debcache.db")
        settings.RPM_CACHE_DIR = os.path.join(self.test_dir, "rpmcache")

        for p in [settings.STORAGE_PATH, settings.REPO_WWW_PATH, settings.KEYRING_PATH, settings.RPM_CACHE_DIR]:
            os.makedirs(p, exist_ok=True)

        self.signing_key = PGPSigningKey.objects.create(
            name="Test Key",
            email="test@example.com",
            fingerprint="BASEREPO_TEST_FP",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(repo_uid="base-repo-test", repo_type="deb", signing_key=self.signing_key)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _make_adapter(self):
        adapter = GenericRepoAdapter(self.repo)
        adapter.build = Build.objects.create(repo=self.repo, build_number=1)
        adapter.packages = []
        return adapter

    def test_buildlog_write_creates_db_entry(self):
        """_buildlog_write saves a BuildLogLine to the database"""
        adapter = self._make_adapter()
        adapter._buildlog_write("test command", "test message", loglevel="info")
        self.assertEqual(BuildLogLine.objects.count(), 1)
        entry = BuildLogLine.objects.get()
        self.assertEqual(entry.command, "test command")
        self.assertEqual(entry.message, "test message")
        self.assertEqual(entry.loglevel, "info")
        self.assertTrue(entry.exec_complete)

    def test_buildlog_write_increments_line_number(self):
        """_buildlog_write increments line_number each call"""
        adapter = self._make_adapter()
        adapter._buildlog_write("cmd1")
        adapter._buildlog_write("cmd2")
        lines = list(BuildLogLine.objects.order_by("line_number"))
        self.assertEqual(lines[0].line_number, 0)
        self.assertEqual(lines[1].line_number, 1)

    def test_buildlog_section_creates_incomplete_entry(self):
        """_buildlog_section creates a log entry with exec_complete=False"""
        adapter = self._make_adapter()
        with adapter._buildlog_section("doing something"):
            entry = BuildLogLine.objects.order_by("-line_number").first()
            self.assertFalse(entry.exec_complete)

    def test_buildlog_section_marks_complete_on_exit(self):
        """_buildlog_section marks entry as complete when context exits"""
        adapter = self._make_adapter()
        with adapter._buildlog_section("doing something") as log_entry:
            log_entry.set_message("finished")

        entry = BuildLogLine.objects.order_by("-line_number").first()
        self.assertTrue(entry.exec_complete)
        self.assertIsNotNone(entry.execution_time_sec)

    def test_buildlog_section_set_loglevel(self):
        """BuildLogEntry.set_loglevel updates the loglevel"""
        adapter = self._make_adapter()
        with adapter._buildlog_section("cmd") as log_entry:
            log_entry.set_loglevel("warning")
        entry = BuildLogLine.objects.order_by("-line_number").first()
        self.assertEqual(entry.loglevel, "warning")

    def test_clean_old_dirs_removes_stale_dirs(self):
        """_clean_old_dirs removes old versioned repo directories"""
        adapter = self._make_adapter()
        adapter.repo_uid = "cleantest"

        keep_dir = "cleantest.000000002"
        old_dir1 = "cleantest.000000001"
        other_dir = "unrelated-dir"

        for d in [keep_dir, old_dir1, other_dir]:
            os.makedirs(os.path.join(settings.REPO_WWW_PATH, d))

        adapter._clean_old_dirs(keep_dir)

        self.assertFalse(os.path.exists(os.path.join(settings.REPO_WWW_PATH, old_dir1)))
        self.assertTrue(os.path.exists(os.path.join(settings.REPO_WWW_PATH, keep_dir)))
        self.assertTrue(os.path.exists(os.path.join(settings.REPO_WWW_PATH, other_dir)))

    def test_save_public_key_writes_file(self):
        """_save_public_key writes the public key PEM to public.gpg in repo dir"""
        adapter = self._make_adapter()
        adapter.pgp_key = self.signing_key

        repo_path = os.path.join(settings.REPO_WWW_PATH, "pubkey_test")
        os.makedirs(repo_path)

        adapter._save_public_key(repo_path)

        gpg_path = os.path.join(repo_path, "public.gpg")
        self.assertTrue(os.path.isfile(gpg_path))
        with open(gpg_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "pub")

    def test_copy_packages_creates_symlinks(self):
        """_copy_packages creates symlinks for each package in dest dir"""
        # Create a fake source file
        src_dir = os.path.join(settings.STORAGE_PATH, "aa")
        os.makedirs(src_dir, exist_ok=True)
        src_file = os.path.join(src_dir, "bbccddee")
        with open(src_file, "w") as f:
            f.write("dummy package")

        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="aa-bbccddee",
            filename="test.deb",
            package_name="test",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="hash1",
        )

        adapter = self._make_adapter()
        adapter.packages = [pkg]

        dest_dir = os.path.join(settings.REPO_WWW_PATH, "symlink_test")
        os.makedirs(dest_dir)

        adapter._copy_packages(dest_dir)

        expected_link = os.path.join(dest_dir, "test.deb")
        self.assertTrue(os.path.islink(expected_link))
        self.assertEqual(os.readlink(expected_link), src_file)

    @patch("subprocess.run")
    def test_execute_commands_returns_true_on_success(self, mock_run):
        """_execute_commands returns True when all commands succeed"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_run.return_value = mock_proc

        adapter = self._make_adapter()
        result = adapter._execute_commands(["echo hello"], settings.REPO_WWW_PATH)
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_execute_commands_returns_false_on_failure(self, mock_run):
        """_execute_commands returns False when a command fails"""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "error output"
        mock_run.return_value = mock_proc

        adapter = self._make_adapter()
        result = adapter._execute_commands(["false"], settings.REPO_WWW_PATH)
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_execute_commands_stops_on_first_failure(self, mock_run):
        """_execute_commands stops after first failing command"""
        mock_proc_fail = MagicMock()
        mock_proc_fail.returncode = 1
        mock_proc_fail.stdout = "fail"
        mock_run.return_value = mock_proc_fail

        adapter = self._make_adapter()
        adapter._execute_commands(["cmd1", "cmd2", "cmd3"], settings.REPO_WWW_PATH)
        self.assertEqual(mock_run.call_count, 1)

    def test_generate_repo_structure_raises_in_base(self):
        """BaseRepoAdapter._generate_repo_structure raises Exception (must be subclassed)"""
        class BareAdapter(BaseRepoAdapter):
            pass

        adapter = BareAdapter(self.repo)
        adapter.build = Build.objects.create(repo=self.repo, build_number=99)
        with self.assertRaises(Exception):
            adapter._generate_repo_structure("/tmp")

    def test_get_repo_instructions_raises_in_base(self):
        """BaseRepoAdapter._get_repo_instructions raises Exception (must be subclassed)"""
        class BareAdapter(BaseRepoAdapter):
            pass

        adapter = BareAdapter(self.repo)
        with self.assertRaises(Exception):
            adapter._get_repo_instructions()


class SetupRepoTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = os.path.join(self.test_dir, "storage")
        settings.REPO_WWW_PATH = os.path.join(self.test_dir, "www")
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        settings.DEB_DB_PATH = os.path.join(self.test_dir, "debcache.db")
        settings.RPM_CACHE_DIR = os.path.join(self.test_dir, "rpmcache")

        for p in [settings.STORAGE_PATH, settings.REPO_WWW_PATH, settings.KEYRING_PATH, settings.RPM_CACHE_DIR]:
            os.makedirs(p, exist_ok=True)

        self.signing_key = PGPSigningKey.objects.create(
            name="SetupKey",
            email="setup@example.com",
            fingerprint="SETUP_REPO_FP_12345",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="setup-test-repo", repo_type="files", signing_key=self.signing_key
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("repo.storage.keyring.PGPKeyring.ensure_key")
    def test_setup_repo_success_creates_symlink(self, mock_ensure_key):
        """setup_repo creates versioned dir, generates structure, and updates symlink"""
        adapter = GenericRepoAdapter(self.repo)
        result = adapter.setup_repo()

        self.assertTrue(result)

        # Check symlink was created
        symlink_path = os.path.join(settings.REPO_WWW_PATH, self.repo.repo_uid)
        self.assertTrue(os.path.islink(symlink_path))

        # DB should record successful build
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.refresh_count, 1)
        build = Build.objects.get(repo=self.repo, build_number=1)
        self.assertEqual(build.completion_status, Build.STATUS_COMPLETE_SUCCESS)

    @patch("repo.storage.keyring.PGPKeyring.ensure_key")
    def test_setup_repo_increments_refresh_count(self, mock_ensure_key):
        """setup_repo increments refresh_count each run"""
        adapter = GenericRepoAdapter(self.repo)
        adapter.setup_repo()
        adapter.setup_repo()

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.refresh_count, 2)

    @patch("repo.storage.keyring.PGPKeyring.ensure_key")
    def test_setup_repo_removes_old_dir_after_second_run(self, mock_ensure_key):
        """setup_repo cleans up the old versioned directory after a refresh"""
        adapter = GenericRepoAdapter(self.repo)
        adapter.setup_repo()

        old_dir = os.path.join(settings.REPO_WWW_PATH, f"{self.repo.repo_uid}.{1:=09}")
        self.assertTrue(os.path.isdir(old_dir))

        adapter2 = GenericRepoAdapter(self.repo)
        adapter2.setup_repo()

        # After second run, first dir should be cleaned
        self.assertFalse(os.path.isdir(old_dir))

    @patch("adapters.repo.generic_repo.GenericRepoAdapter._generate_repo_structure", return_value=False)
    @patch("repo.storage.keyring.PGPKeyring.ensure_key")
    def test_setup_repo_records_failure_status(self, mock_ensure_key, mock_gen):
        """setup_repo sets STATUS_COMPLETE_ERROR when _generate_repo_structure fails"""
        adapter = GenericRepoAdapter(self.repo)
        result = adapter.setup_repo()

        self.assertFalse(result)
        build = Build.objects.get(repo=self.repo)
        self.assertEqual(build.completion_status, Build.STATUS_COMPLETE_ERROR)


class GenericRepoAdapterTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = os.path.join(self.test_dir, "storage")
        settings.REPO_WWW_PATH = os.path.join(self.test_dir, "www")
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")

        for p in [settings.STORAGE_PATH, settings.REPO_WWW_PATH, settings.KEYRING_PATH]:
            os.makedirs(p, exist_ok=True)

        self.signing_key = PGPSigningKey.objects.create(
            name="GenKey",
            email="gen@example.com",
            fingerprint="GEN_REPO_FP",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        self.repo = Repository.objects.create(
            repo_uid="generic-adapter-test", repo_type="files", signing_key=self.signing_key
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_repo_instructions_returns_base_url(self):
        """GenericRepoAdapter._get_repo_instructions returns the base URL"""
        adapter = GenericRepoAdapter(self.repo)
        instructions = adapter._get_repo_instructions()
        self.assertIn(self.repo.repo_uid, instructions)

    def test_generate_repo_structure_returns_true(self):
        """GenericRepoAdapter._generate_repo_structure returns True"""
        adapter = GenericRepoAdapter(self.repo)
        adapter.build = Build.objects.create(repo=self.repo, build_number=1)
        adapter.packages = []

        repo_path = os.path.join(settings.REPO_WWW_PATH, "gen_test_dir")
        os.makedirs(repo_path)

        result = adapter._generate_repo_structure(repo_path)
        self.assertTrue(result)
