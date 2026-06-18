# Copyright 2022 by Open Kilt LLC. All rights reserved.
from django.test import TestCase
from repo.models import Repository, Package, PGPSigningKey, Build, BuildLogLine
from adapters.file.deb_adapter import DebFileAdapter
from adapters.repo.deb_repo import DebRepoAdapter
from adapters.file.rpm_adapter import RpmFileAdapter
from adapters.repo.rpm_repo import RpmRepoAdapter
from django.conf import settings
import os
from unittest.mock import patch, MagicMock
import tempfile
import shutil

class AdapterTestCase(TestCase):
    def setUp(self):
        self.repo_uid = 'test-deb-repo'
        self.signing_key = PGPSigningKey.objects.create(
            name="Test Key",
            email="test@example.com",
            fingerprint="8EC5273D32F78A238F54CBEB66633B39A053B24A",
            public_key_pem="dummy public",
            private_key_pem="dummy private"
        )
        self.repo = Repository.objects.create(
            repo_uid=self.repo_uid,
            repo_type='deb',
            signing_key=self.signing_key
        )
        
        # Setup paths
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = os.path.join(self.test_dir, "storage")
        settings.REPO_WWW_PATH = os.path.join(self.test_dir, "www")
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        settings.DEB_DB_PATH = os.path.join(self.test_dir, "debcache.db")
        settings.RPM_CACHE_DIR = os.path.join(self.test_dir, "rpmcache")
        
        for p in [settings.STORAGE_PATH, settings.REPO_WWW_PATH, settings.KEYRING_PATH, settings.RPM_CACHE_DIR]:
            if not os.path.exists(p):
                os.makedirs(p)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_deb_file_adapter_metadata(self):
        """Test that DebFileAdapter extracts correct metadata from a .deb file"""
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, 'unittest_files/hello-world_1.0.0_all.deb')
        
        adapter = DebFileAdapter(deb_path)
        self.assertEqual(adapter.get_name(), 'hello-world')
        self.assertEqual(adapter.get_version(), '1.0.0')
        self.assertEqual(adapter.get_architecture(), 'all')

    @patch('subprocess.run')
    @patch('repo.storage.keyring.PGPKeyring.ensure_key')
    def test_deb_repo_generation(self, mock_ensure_key, mock_run):
        """Test that DebRepoAdapter triggers the correct commands for repo generation"""
        # Mock successful subprocess execution
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Command output"
        mock_run.return_value = mock_proc
        
        # Add a package to the repo
        Package.objects.create(
            repo=self.repo,
            package_uid="test-pkg-uid",
            filename="hello-world_1.0.0_all.deb",
            package_name="hello-world",
            version="1.0.0",
            architecture="all",
            upload_date="2022-01-01T00:00:00Z",
            checksum_sha512="dummy"
        )
        
        # Create a dummy file for symlinking
        pkg_file_path = os.path.join(settings.STORAGE_PATH, "test/pkg/uid")
        os.makedirs(os.path.dirname(pkg_file_path), exist_ok=True)
        with open(pkg_file_path, "w") as f:
            f.write("dummy package content")

        adapter = DebRepoAdapter(self.repo)
        # Create a build object as BaseRepoAdapter needs it for logging
        adapter.build = Build.objects.create(repo=self.repo, build_number=1)
        adapter.packages = Package.objects.filter(repo=self.repo)
        
        repo_path = os.path.join(settings.REPO_WWW_PATH, "test_repo_dir")
        os.makedirs(repo_path, exist_ok=True)
        
        success = adapter._generate_repo_structure(repo_path)
        
        self.assertTrue(success)
        
        # Check if key commands were called (apt-ftparchive, gpg)
        called_commands = [call.args[0] for call in mock_run.call_args_list]
        self.assertTrue(any("apt-ftparchive" in cmd for cmd in called_commands))
        self.assertTrue(any("gpg" in cmd for cmd in called_commands))
        self.assertTrue(any("--local-user 8EC5273D32F78A238F54CBEB66633B39A053B24A" in cmd for cmd in called_commands))

    def test_repo_instructions(self):
        """Test that repo instructions are correctly generated"""
        adapter = DebRepoAdapter(self.repo)
        instructions = adapter._get_repo_instructions()
        self.assertIn("apt update", instructions)
        self.assertIn(f"openrepo-{self.repo_uid}.list", instructions)
        self.assertIn("signed-by=/usr/share/keyrings/openrepo-test-deb-repo.gpg", instructions)

    @patch('rpmfile.open')
    def test_rpm_file_adapter_metadata(self, mock_rpm_open):
        """Test that RpmFileAdapter extracts correct metadata from a mocked RPM file"""
        mock_rpm = MagicMock()
        mock_rpm.headers.get.side_effect = lambda x: {
            'name': b'test-pkg',
            'version': b'1.2.3',
            'release': b'1',
            'arch': b'x86_64',
            'buildtime': 1600000000,
            'description': b'Test description'
        }.get(x)
        
        # Configure the context manager mock
        mock_rpm_open.return_value.__enter__.return_value = mock_rpm
        
        settings.RPM_VERSION_IGNORE_BUILD_NUM = False
        adapter = RpmFileAdapter("dummy.rpm")
        
        self.assertEqual(adapter.get_name(), 'test-pkg')
        self.assertEqual(adapter.get_version(), '1.2.3.1')
        self.assertEqual(adapter.get_architecture(), 'x86_64')

    def test_copy_packages_with_same_filename_different_versions(self):
        """Test that _copy_packages creates unique pool symlinks when multiple
        packages share the same original filename but differ in version."""
        pkg1 = Package.objects.create(
            repo=self.repo,
            package_uid="pkg-one-uid",
            filename="kumomta.Ubuntu22.04.deb",
            package_name="kumomta",
            version="1.0.0",
            architecture="all",
            upload_date="2022-01-01T00:00:00Z",
            checksum_sha512="aaaa"
        )
        pkg2 = Package.objects.create(
            repo=self.repo,
            package_uid="pkg-two-uid",
            filename="kumomta.Ubuntu22.04.deb",
            package_name="kumomta",
            version="2.0.0",
            architecture="all",
            upload_date="2022-01-02T00:00:00Z",
            checksum_sha512="bbbb"
        )

        for pkg in [pkg1, pkg2]:
            rel = pkg.relative_path()
            full = os.path.join(settings.STORAGE_PATH, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as f:
                f.write(f"content {pkg.version}")

        adapter = DebRepoAdapter(self.repo)
        adapter.build = Build.objects.create(repo=self.repo, build_number=1)
        adapter.packages = Package.objects.filter(repo=self.repo)

        dest = os.path.join(settings.REPO_WWW_PATH, "pool_main")
        os.makedirs(dest, exist_ok=True)
        adapter._copy_packages(dest)

        pool_files = sorted(os.listdir(dest))
        self.assertEqual(len(pool_files), 2,
                         "Expected both versions to have unique pool filenames")

        expected = ["kumomta_1.0.0_all.deb", "kumomta_2.0.0_all.deb"]
        self.assertEqual(pool_files, expected)

        expected_targets = {
            "kumomta_1.0.0_all.deb": os.path.join(settings.STORAGE_PATH, pkg1.relative_path()),
            "kumomta_2.0.0_all.deb": os.path.join(settings.STORAGE_PATH, pkg2.relative_path()),
        }
        for pool_name, expected_target in expected_targets.items():
            link_path = os.path.join(dest, pool_name)
            self.assertTrue(os.path.islink(link_path),
                            f"{pool_name} should be a symlink")
            self.assertEqual(os.readlink(link_path), expected_target)
            with open(expected_target) as f:
                self.assertIn(pool_name.split("_")[1], f.read())

    @patch('subprocess.run')
    @patch('repo.storage.keyring.PGPKeyring.ensure_key')
    def test_rpm_repo_generation(self, mock_ensure_key, mock_run):
        """Test that RpmRepoAdapter triggers the correct commands (createrepo, gpg)"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Command output"
        mock_run.return_value = mock_proc
        
        repo_rpm = Repository.objects.create(
            repo_uid="test-rpm-repo",
            repo_type='rpm',
            signing_key=self.signing_key
        )
        
        adapter = RpmRepoAdapter(repo_rpm)
        # Create a build object as BaseRepoAdapter needs it for logging
        adapter.build = Build.objects.create(repo=repo_rpm, build_number=1)
        adapter.packages = [] # No packages for this simple test
        
        repo_path = os.path.join(settings.REPO_WWW_PATH, "test_rpm_dir")
        os.makedirs(repo_path, exist_ok=True)
        
        success = adapter._generate_repo_structure(repo_path)
        
        self.assertTrue(success)
        called_commands = [call.args[0] for call in mock_run.call_args_list]
        self.assertTrue(any("createrepo" in cmd for cmd in called_commands))
        self.assertTrue(any("gpg" in cmd for cmd in called_commands) and any("--detach-sign" in cmd for cmd in called_commands))
