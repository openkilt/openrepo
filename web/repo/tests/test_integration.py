import os
import time
import gzip
import shutil
import subprocess
import tempfile
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from repo.models import Repository, Package, PGPSigningKey, Build
from rest_framework.authtoken.models import Token
from unittest.mock import patch


def _gen_test_key(homedir):
    batch = os.path.join(homedir, 'keygen.batch')
    with open(batch, 'w') as f:
        f.write(
            'Key-Type: RSA\nKey-Length: 2048\n'
            'Name-Real: Integration Test\n'
            'Name-Email: test@example.com\n'
            'Expire-Date: 0\n%no-protection\n%commit\n'
        )
    subprocess.run(
        ['gpg', '--homedir', homedir, '--batch', '--gen-key', batch],
        capture_output=True,
    )
    result = subprocess.run(
        ['gpg', '--homedir', homedir, '--list-secret-keys', '--with-colons'],
        capture_output=True, text=True,
    )
    fp = None
    for line in result.stdout.splitlines():
        if line.startswith('fpr:'):
            fp = line.split(':')[9]
            break
    pub = subprocess.run(
        ['gpg', '--homedir', homedir, '--armor', '--export', fp],
        capture_output=True,
    ).stdout.decode()
    sec = subprocess.run(
        ['gpg', '--homedir', homedir, '--armor', '--export-secret-keys', fp],
        capture_output=True,
    ).stdout.decode()
    return fp, pub, sec


class DebRepoIntegrationTest(APITestCase):
    """End-to-end tests using real GPG, apt-ftparchive, and gpg signing"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gnupg_home = tempfile.mkdtemp()
        cls.fingerprint, cls.public_key_pem, cls.private_key_pem = _gen_test_key(cls.gnupg_home)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.gnupg_home, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='int-admin', password='p')
        self.token = Token.objects.get(user=self.admin).key
        self.auth = f'Token {self.token}'

        self.signing_key = PGPSigningKey.objects.create(
            name="Integration Key",
            email="test@example.com",
            fingerprint=self.fingerprint,
            public_key_pem=self.public_key_pem,
            private_key_pem=self.private_key_pem,
        )

        self.storage = tempfile.mkdtemp()
        self.www = tempfile.mkdtemp()
        self.deb_cache = tempfile.mkdtemp()
        self.rpm_cache = tempfile.mkdtemp()

        self._old_storage = settings.STORAGE_PATH
        self._old_www = settings.REPO_WWW_PATH
        self._old_keyring = settings.KEYRING_PATH
        self._old_deb_db = settings.DEB_DB_PATH
        self._old_rpm_cache = settings.RPM_CACHE_DIR

        settings.STORAGE_PATH = self.storage
        settings.REPO_WWW_PATH = self.www
        settings.KEYRING_PATH = self.gnupg_home
        settings.DEB_DB_PATH = os.path.join(self.deb_cache, 'debcache.db')
        settings.RPM_CACHE_DIR = self.rpm_cache

    def tearDown(self):
        settings.STORAGE_PATH = self._old_storage
        settings.REPO_WWW_PATH = self._old_www
        settings.KEYRING_PATH = self._old_keyring
        settings.DEB_DB_PATH = self._old_deb_db
        settings.RPM_CACHE_DIR = self._old_rpm_cache

        shutil.rmtree(self.storage, ignore_errors=True)
        shutil.rmtree(self.www, ignore_errors=True)
        shutil.rmtree(self.deb_cache, ignore_errors=True)
        shutil.rmtree(self.rpm_cache, ignore_errors=True)

    @patch('threading.Thread.start', lambda self: self.run())
    def test_full_deb_upload_and_repo_generation(self):
        """Upload a real .deb, generate a Debian repo, verify pool file and Packages.gz"""
        response = self.client.post('/api/repos/', {
            'repo_uid': 'int-deb', 'repo_type': 'deb',
            'signing_key': self.fingerprint,
        }, HTTP_AUTHORIZATION=self.auth, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, 'unittest_files/hello-world_1.0.0_all.deb')
        with open(deb_path, 'rb') as f:
            content = f.read()
        upload_file = SimpleUploadedFile('hello-world_1.0.0_all.deb', content,
                                         content_type='application/octet-stream')

        response = self.client.post(
            '/api/int-deb/upload/',
            {'package_file': upload_file},
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        task_id = response.data['task_id']

        for _ in range(50):
            status_resp = self.client.get(f'/api/upload-status/{task_id}/',
                                          HTTP_AUTHORIZATION=self.auth)
            if status_resp.data['status'] in ('completed', 'failed'):
                break
            time.sleep(0.2)

        self.assertEqual(status_resp.data['status'], 'completed')

        package = Package.objects.get()
        self.assertEqual(package.package_name, 'hello-world')
        self.assertEqual(package.version, '1.0.0')

        disk_path = os.path.join(self.storage, package.relative_path())
        self.assertTrue(os.path.isfile(disk_path))

        repo_dir = os.path.join(self.www, 'int-deb.1')
        os.makedirs(repo_dir, exist_ok=True)

        from adapters.repo import get_repo_adapter
        repo_obj = Repository.objects.get(repo_uid='int-deb')
        build = Build.objects.create(repo=repo_obj, build_number=1)
        adapter = get_repo_adapter(repo_obj)
        adapter.build = build
        adapter.packages = Package.objects.filter(repo=repo_obj)

        result = adapter._generate_repo_structure(repo_dir)
        self.assertTrue(result)

        self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'public.gpg')))

        release_path = os.path.join(repo_dir, 'dists/stable/Release')
        self.assertTrue(os.path.isfile(release_path))

        release_gpg = os.path.join(repo_dir, 'dists/stable/Release.gpg')
        self.assertTrue(os.path.isfile(release_gpg))

        inrelease_path = os.path.join(repo_dir, 'dists/stable/InRelease')
        self.assertTrue(os.path.isfile(inrelease_path))

        pool_file = os.path.join(repo_dir, 'pool/main/hello-world_1.0.0_all.deb')
        self.assertTrue(os.path.lexists(pool_file))
        self.assertEqual(os.path.realpath(pool_file), disk_path)

        packages_gz = os.path.join(repo_dir, 'dists/stable/main/binary-any/Packages.gz')
        self.assertTrue(os.path.isfile(packages_gz))
        with gzip.open(packages_gz, 'rt', encoding='utf-8', errors='replace') as f:
            pkgs_content = f.read()
        self.assertIn('Package: hello-world', pkgs_content)
        self.assertIn('Version: 1.0.0', pkgs_content)

    @patch('threading.Thread.start', lambda self: self.run())
    def test_signature_verification(self):
        """Upload .deb, generate repo, and verify Release.gpg is valid against public key"""
        import gnupg

        response = self.client.post('/api/repos/', {
            'repo_uid': 'sig-repo', 'repo_type': 'deb',
            'signing_key': self.fingerprint,
        }, HTTP_AUTHORIZATION=self.auth, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, 'unittest_files/hello-world_1.0.0_all.deb')
        with open(deb_path, 'rb') as f:
            content = f.read()
        upload_file = SimpleUploadedFile('hello-world_1.0.0_all.deb', content,
                                         content_type='application/octet-stream')

        response = self.client.post(
            '/api/sig-repo/upload/',
            {'package_file': upload_file},
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        task_id = response.data['task_id']

        for _ in range(50):
            status_resp = self.client.get(f'/api/upload-status/{task_id}/',
                                          HTTP_AUTHORIZATION=self.auth)
            if status_resp.data['status'] in ('completed', 'failed'):
                break
            time.sleep(0.2)

        self.assertEqual(status_resp.data['status'], 'completed')

        repo_dir = os.path.join(self.www, 'sig-repo.1')
        os.makedirs(repo_dir, exist_ok=True)

        from adapters.repo import get_repo_adapter
        repo_obj = Repository.objects.get(repo_uid='sig-repo')
        build = Build.objects.create(repo=repo_obj, build_number=1)
        adapter = get_repo_adapter(repo_obj)
        adapter.build = build
        adapter.packages = Package.objects.filter(repo=repo_obj)

        result = adapter._generate_repo_structure(repo_dir)
        self.assertTrue(result)

        release_path = os.path.join(repo_dir, 'dists/stable/Release')
        release_gpg = os.path.join(repo_dir, 'dists/stable/Release.gpg')

        import subprocess as _sp
        verify = _sp.run(
            ['gpg', '--homedir', self.gnupg_home, '--verify', release_gpg, release_path],
            capture_output=True, text=True,
        )
        self.assertEqual(verify.returncode, 0,
                         f"Release.gpg should verify: {verify.stderr}")

    def test_pgp_key_generation_and_signing(self):
        """Generate a PGP key via PGPKeyring and sign a file with it"""
        from repo.storage.keyring import PGPKeyring

        keyring = PGPKeyring()
        new_key = keyring.generate_key("E2E Test User", "e2e@example.com")
        self.assertIsNotNone(new_key.fingerprint)

        import tempfile
        input_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        input_file.write("Hello, world!")
        input_file.close()

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.asc')
        output_file.close()

        keyring.detach_sign_file(new_key, output_file.name, input_file.name)
        self.assertTrue(os.path.isfile(output_file.name))

        with open(output_file.name, 'r') as f:
            sig_content = f.read()
        self.assertIn('BEGIN PGP SIGNATURE', sig_content)

        os.unlink(input_file.name)
        os.unlink(output_file.name)

        new_key.delete()


class RpmRepoIntegrationTest(APITestCase):
    """End-to-end test using real createrepo_c with a generated RPM package"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gnupg_home = tempfile.mkdtemp()
        cls.fingerprint, cls.public_key_pem, cls.private_key_pem = _gen_test_key(cls.gnupg_home)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.gnupg_home, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        import subprocess as _sp
        _sp.run(['gpgconf', '--homedir', self.gnupg_home, '--kill', 'gpg-agent'],
                capture_output=True)
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='rpm-admin', password='p')
        self.token = Token.objects.get(user=self.admin).key
        self.auth = f'Token {self.token}'

        self.signing_key = PGPSigningKey.objects.create(
            name="RPM Key", email="rpm@example.com",
            fingerprint=self.fingerprint,
            public_key_pem=self.public_key_pem,
            private_key_pem=self.private_key_pem,
        )

        self.storage = tempfile.mkdtemp()
        self.www = tempfile.mkdtemp()
        self.rpm_cache = tempfile.mkdtemp()

        self._old_storage = settings.STORAGE_PATH
        self._old_www = settings.REPO_WWW_PATH
        self._old_keyring = settings.KEYRING_PATH
        self._old_rpm_cache = settings.RPM_CACHE_DIR

        settings.STORAGE_PATH = self.storage
        settings.REPO_WWW_PATH = self.www
        settings.KEYRING_PATH = self.gnupg_home
        settings.RPM_CACHE_DIR = self.rpm_cache

    def tearDown(self):
        settings.STORAGE_PATH = self._old_storage
        settings.REPO_WWW_PATH = self._old_www
        settings.KEYRING_PATH = self._old_keyring
        settings.RPM_CACHE_DIR = self._old_rpm_cache

        shutil.rmtree(self.storage, ignore_errors=True)
        shutil.rmtree(self.www, ignore_errors=True)
        shutil.rmtree(self.rpm_cache, ignore_errors=True)

    def test_rpm_repo_generation_with_real_createrepo(self):
        """Create a package entry and generate an RPM repo with real createrepo_c"""
        repo = Repository.objects.create(
            repo_uid='int-rpm', repo_type='rpm',
            signing_key=self.signing_key,
        )

        package_file = os.path.join(self.storage, 'te/st')
        os.makedirs(os.path.dirname(package_file), exist_ok=True)
        with open(package_file, 'w') as f:
            f.write('rpm content')

        now = __import__('datetime').datetime.now(tz=__import__('datetime').timezone.utc)
        Package.objects.create(
            repo=repo,
            package_uid='te-st',
            filename='test-package-1.0-1.noarch.rpm',
            package_name='test-package',
            version='1.0-1',
            architecture='noarch',
            upload_date=now,
            checksum_sha512='dummy-sha',
        )

        repo_dir = os.path.join(self.www, 'int-rpm.1')
        os.makedirs(repo_dir, exist_ok=True)

        from adapters.repo import get_repo_adapter
        build = Build.objects.create(repo=repo, build_number=1)
        adapter = get_repo_adapter(repo)
        adapter.build = build
        adapter.packages = Package.objects.filter(repo=repo)

        result = adapter._generate_repo_structure(repo_dir)
        self.assertTrue(result)

        self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'public.gpg')))

        repomd_path = os.path.join(repo_dir, 'repodata/repomd.xml')
        self.assertTrue(os.path.isfile(repomd_path))

        # Verify repo metadata was generated (packages="0" because the pool file isn't a valid RPM)
        import xml.etree.ElementTree as ET
        tree = ET.parse(repomd_path)
        ns = {'r': 'http://linux.duke.edu/metadata/repo'}
        self.assertIsNotNone(tree.find(".//r:data[@type='primary']", ns))

        pool_file = os.path.join(repo_dir, 'test-package_1.0-1_noarch.rpm')
        self.assertTrue(os.path.lexists(pool_file))
