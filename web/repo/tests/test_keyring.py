# Copyright 2022 by Open Kilt LLC. All rights reserved.
import os
import tempfile
from unittest.mock import MagicMock, call, patch

from django.conf import settings
from django.test import TestCase

from repo.models import PGPSigningKey
from repo.storage.keyring import PGPKeyring


class PGPKeyringInitTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")

    def test_creates_keyring_dir_if_missing(self):
        """PGPKeyring creates keyring directory when it does not exist"""
        with patch("gnupg.GPG") as mock_gpg_cls:
            mock_gpg_cls.return_value = MagicMock()
            ring = PGPKeyring()
            self.assertTrue(os.path.isdir(settings.KEYRING_PATH))

    def test_init_with_gnupghome_kwarg(self):
        """PGPKeyring tries gnupghome first, falls back to homedir"""
        os.makedirs(settings.KEYRING_PATH, exist_ok=True)
        mock_gpg = MagicMock()
        with patch("gnupg.GPG", return_value=mock_gpg) as mock_gpg_cls:
            ring = PGPKeyring()
            mock_gpg_cls.assert_called_with(gnupghome=settings.KEYRING_PATH)

    def test_init_fallback_to_homedir(self):
        """PGPKeyring falls back to homedir= kwarg when gnupghome raises TypeError"""
        os.makedirs(settings.KEYRING_PATH, exist_ok=True)
        mock_gpg = MagicMock()
        with patch("gnupg.GPG", side_effect=[TypeError("no gnupghome"), mock_gpg]):
            ring = PGPKeyring()
            self.assertEqual(ring.gpg, mock_gpg)


class PGPKeyringGenerateKeyTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        os.makedirs(settings.KEYRING_PATH)

    @patch("gnupg.GPG")
    def test_generate_key_creates_db_entry(self, mock_gpg_cls):
        """generate_key saves a new PGPSigningKey to the database"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg

        fake_key = MagicMock()
        fake_key.fingerprint = "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
        mock_gpg.gen_key.return_value = fake_key
        mock_gpg.export_keys.side_effect = ["-----PUBLIC KEY-----", "-----PRIVATE KEY-----"]

        ring = PGPKeyring()
        result = ring.generate_key("Test User", "test@example.com")

        self.assertEqual(PGPSigningKey.objects.count(), 1)
        saved = PGPSigningKey.objects.get()
        self.assertEqual(saved.fingerprint, fake_key.fingerprint)
        self.assertEqual(saved.name, "Test User")
        self.assertEqual(saved.email, "test@example.com")
        self.assertEqual(result, saved)

    @patch("gnupg.GPG")
    def test_generate_key_calls_gen_key_input(self, mock_gpg_cls):
        """generate_key builds RSA-4096 key input with correct parameters"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg
        fake_key = MagicMock()
        fake_key.fingerprint = "FP123"
        mock_gpg.gen_key.return_value = fake_key
        mock_gpg.export_keys.side_effect = ["pub", "priv"]

        ring = PGPKeyring()
        ring.generate_key("Alice", "alice@example.com")

        mock_gpg.gen_key_input.assert_called_once_with(
            key_type="RSA",
            key_length=4096,
            expire_date="50y",
            name_real="Alice",
            name_email="alice@example.com",
            no_protection=True,
        )


class PGPKeyringDeleteTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        os.makedirs(settings.KEYRING_PATH)

    @patch("gnupg.GPG")
    def test_delete_calls_gpg_delete_keys_twice(self, mock_gpg_cls):
        """delete() removes private then public key from the keyring"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg

        ring = PGPKeyring()
        ring.delete("FINGERPRINT123")

        expected = [
            call("FINGERPRINT123", secret=True, passphrase=""),
            call("FINGERPRINT123", secret=False),
        ]
        mock_gpg.delete_keys.assert_has_calls(expected)


class PGPKeyringEnsureKeyTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        os.makedirs(settings.KEYRING_PATH)

        self.pgp_key = PGPSigningKey(
            fingerprint="ABCDEF12345",
            private_key_pem="-----PRIVATE-----",
            public_key_pem="-----PUBLIC-----",
            name="Key",
            email="key@example.com",
        )

    @patch("gnupg.GPG")
    def test_ensure_key_imports_when_not_found(self, mock_gpg_cls):
        """ensure_key imports and trusts the key when not already in keyring"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg
        mock_gpg.list_keys.return_value = []

        ring = PGPKeyring()
        ring.ensure_key(self.pgp_key)

        mock_gpg.import_keys.assert_called_once_with(self.pgp_key.private_key_pem)
        mock_gpg.trust_keys.assert_called_once_with(self.pgp_key.fingerprint, "TRUST_ULTIMATE")

    @patch("gnupg.GPG")
    def test_ensure_key_skips_import_when_already_present(self, mock_gpg_cls):
        """ensure_key does not import when key already exists in keyring"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg
        mock_gpg.list_keys.return_value = [{"fingerprint": "ABCDEF12345"}]

        ring = PGPKeyring()
        ring.ensure_key(self.pgp_key)

        mock_gpg.import_keys.assert_not_called()

    @patch("gnupg.GPG")
    def test_ensure_key_with_multiple_keys_finds_correct(self, mock_gpg_cls):
        """ensure_key correctly matches fingerprint among multiple keys"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg
        mock_gpg.list_keys.return_value = [
            {"fingerprint": "OTHER1"},
            {"fingerprint": "ABCDEF12345"},
        ]

        ring = PGPKeyring()
        ring.ensure_key(self.pgp_key)

        mock_gpg.import_keys.assert_not_called()


class PGPKeyringDetachSignTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        os.makedirs(settings.KEYRING_PATH)

    @patch("gnupg.GPG")
    def test_detach_sign_file_calls_sign(self, mock_gpg_cls):
        """detach_sign_file opens the input file and calls gpg.sign_file"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg

        # Create a real temp file to open
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir=self.test_dir) as f:
            f.write("some content")
            input_path = f.name

        pgp_key = MagicMock()
        pgp_key.fingerprint = "MYFP123"

        ring = PGPKeyring()
        ring.detach_sign_file(pgp_key, "/tmp/out.sig", input_path)

        mock_gpg.sign_file.assert_called_once()
        _, kwargs = mock_gpg.sign_file.call_args
        self.assertEqual(kwargs["keyid"], "MYFP123")
        self.assertTrue(kwargs["detach"])
        self.assertFalse(kwargs["clearsign"])
        self.assertEqual(kwargs["output"], "/tmp/out.sig")

    @patch("gnupg.GPG")
    def test_detach_sign_file_clearsign_param(self, mock_gpg_cls):
        """detach_sign_file passes clear_sign=True when requested"""
        mock_gpg = MagicMock()
        mock_gpg_cls.return_value = mock_gpg

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir=self.test_dir) as f:
            f.write("content")
            input_path = f.name

        pgp_key = MagicMock()
        pgp_key.fingerprint = "FP"

        ring = PGPKeyring()
        ring.detach_sign_file(pgp_key, "/tmp/out.sig", input_path, clear_sign=True)

        _, kwargs = mock_gpg.sign_file.call_args
        self.assertTrue(kwargs["clearsign"])
