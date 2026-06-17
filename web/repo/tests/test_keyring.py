from django.test import TestCase
from django.conf import settings
from repo.models import PGPSigningKey
from repo.storage.keyring import PGPKeyring
from unittest.mock import patch, MagicMock
import tempfile, os, shutil


class PGPKeyringPassphraseTestCase(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")

        self.key_no_pass = PGPSigningKey.objects.create(
            name="No Passphrase Key",
            email="nopass@example.com",
            fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
            public_key_pem="dummy public no pass",
            private_key_pem="dummy private no pass",
            passphrase=""
        )
        self.key_with_pass = PGPSigningKey.objects.create(
            name="With Passphrase Key",
            email="withpass@example.com",
            fingerprint="FFFF6666GGGG7777HHHH8888IIII9999JJJJ0000",
            public_key_pem="dummy public with pass",
            private_key_pem="dummy private with pass",
            passphrase="my secret passphrase"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)


class PGPKeyringPassphraseUnitTest(PGPKeyringPassphraseTestCase):

    @patch('repo.storage.keyring.gnupg')
    def test_ensure_key_no_passphrase_passes_none(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.list_keys.return_value = []
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        keyring.ensure_key(self.key_no_pass)

        mock_gpg.import_keys.assert_called_once_with(
            self.key_no_pass.private_key_pem, passphrase=None
        )

    @patch('repo.storage.keyring.gnupg')
    def test_ensure_key_with_passphrase_passes_it_through(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.list_keys.return_value = []
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        keyring.ensure_key(self.key_with_pass)

        mock_gpg.import_keys.assert_called_once_with(
            self.key_with_pass.private_key_pem,
            passphrase=self.key_with_pass.passphrase
        )

    @patch('repo.storage.keyring.gnupg')
    def test_ensure_key_skips_import_when_key_already_present(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.list_keys.return_value = [
            {'fingerprint': self.key_no_pass.fingerprint}
        ]
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        keyring.ensure_key(self.key_no_pass)

        mock_gpg.import_keys.assert_not_called()

    @patch('repo.storage.keyring.gnupg')
    def test_detach_sign_no_passphrase_passes_none(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        input_path = os.path.join(self.test_dir, "input.txt")
        output_path = os.path.join(self.test_dir, "output.asc")
        with open(input_path, "w") as f:
            f.write("content to sign")

        keyring.detach_sign_file(self.key_no_pass, output_path, input_path)

        mock_gpg.sign_file.assert_called_once()
        _, kwargs = mock_gpg.sign_file.call_args
        self.assertIsNone(kwargs['passphrase'])
        self.assertEqual(kwargs['keyid'], self.key_no_pass.fingerprint)

    @patch('repo.storage.keyring.gnupg')
    def test_detach_sign_with_passphrase_passes_it_through(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        input_path = os.path.join(self.test_dir, "input.txt")
        output_path = os.path.join(self.test_dir, "output.asc")
        with open(input_path, "w") as f:
            f.write("content to sign")

        keyring.detach_sign_file(self.key_with_pass, output_path, input_path)

        mock_gpg.sign_file.assert_called_once()
        _, kwargs = mock_gpg.sign_file.call_args
        self.assertEqual(kwargs['passphrase'], self.key_with_pass.passphrase)

    @patch('repo.storage.keyring.gnupg')
    def test_delete_no_passphrase_passes_empty_string(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        keyring.delete(self.key_no_pass.fingerprint)

        mock_gpg.delete_keys.assert_any_call(
            self.key_no_pass.fingerprint, secret=True, passphrase=''
        )

    @patch('repo.storage.keyring.gnupg')
    def test_delete_with_passphrase_passes_it_through(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gnupg.GPG.return_value = mock_gpg

        keyring = PGPKeyring()
        keyring.delete(
            self.key_with_pass.fingerprint,
            passphrase=self.key_with_pass.passphrase
        )

        mock_gpg.delete_keys.assert_any_call(
            self.key_with_pass.fingerprint, secret=True,
            passphrase=self.key_with_pass.passphrase
        )
