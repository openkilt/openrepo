from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from repo.models import PGPSigningKey
from unittest.mock import patch, MagicMock
from io import StringIO
import tempfile, os, shutil


class ImportPGPPrivateKeyCommandTest(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.KEYRING_PATH = os.path.join(self.test_dir, "keyring")
        self.key_path = os.path.join(self.test_dir, "private.asc")
        with open(self.key_path, "w") as f:
            f.write("-----BEGIN PGP PRIVATE KEY BLOCK-----\ndummy key data\n-----END PGP PRIVATE KEY BLOCK-----")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('repo.management.commands.import_pgp_private_key.gnupg')
    def test_import_without_passphrase(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.encoding = 'utf-8'
        mock_gnupg.GPG.return_value = mock_gpg

        mock_import_result = MagicMock()
        mock_import_result.count = 1
        mock_gpg.import_keys.return_value = mock_import_result

        mock_key = MagicMock()
        mock_key.fingerprints = ["AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"]
        mock_key.__getitem__.side_effect = lambda key: {
            'fingerprint': "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
            'uids': ["Test User <test@example.com>"]
        }.get(key)
        mock_gpg.scan_keys.return_value = [mock_key]

        mock_gpg.export_keys.return_value = "-----BEGIN PGP PUBLIC KEY BLOCK-----\nfake public\n-----END PGP PUBLIC KEY BLOCK-----"

        call_command('import_pgp_private_key', self.key_path)

        mock_gpg.import_keys.assert_called_once_with(
            "-----BEGIN PGP PRIVATE KEY BLOCK-----\ndummy key data\n-----END PGP PRIVATE KEY BLOCK-----",
            passphrase=None
        )

        key = PGPSigningKey.objects.get(fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
        self.assertEqual(key.passphrase, "")
        self.assertEqual(key.name, "Test User")
        self.assertEqual(key.email, "test@example.com")

    @patch('repo.management.commands.import_pgp_private_key.gnupg')
    def test_import_with_passphrase(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.encoding = 'utf-8'
        mock_gnupg.GPG.return_value = mock_gpg

        mock_import_result = MagicMock()
        mock_import_result.count = 1
        mock_gpg.import_keys.return_value = mock_import_result

        mock_key = MagicMock()
        mock_key.fingerprints = ["FFFF6666GGGG7777HHHH8888IIII9999JJJJ0000"]
        mock_key.__getitem__.side_effect = lambda key: {
            'fingerprint': "FFFF6666GGGG7777HHHH8888IIII9999JJJJ0000",
            'uids': ["Secure User <secure@example.com>"]
        }.get(key)
        mock_gpg.scan_keys.return_value = [mock_key]

        mock_gpg.export_keys.return_value = "-----BEGIN PGP PUBLIC KEY BLOCK-----\nfake public\n-----END PGP PUBLIC KEY BLOCK-----"

        call_command('import_pgp_private_key', self.key_path, '--passphrase', 'my secret passphrase')

        mock_gpg.import_keys.assert_called_once_with(
            "-----BEGIN PGP PRIVATE KEY BLOCK-----\ndummy key data\n-----END PGP PRIVATE KEY BLOCK-----",
            passphrase='my secret passphrase'
        )

        key = PGPSigningKey.objects.get(fingerprint="FFFF6666GGGG7777HHHH8888IIII9999JJJJ0000")
        self.assertEqual(key.passphrase, "my secret passphrase")
        self.assertEqual(key.name, "Secure User")
        self.assertEqual(key.email, "secure@example.com")

    @patch('repo.management.commands.import_pgp_private_key.gnupg')
    def test_import_failure_when_key_not_imported(self, mock_gnupg):
        mock_gpg = MagicMock()
        mock_gpg.encoding = 'utf-8'
        mock_gnupg.GPG.return_value = mock_gpg

        mock_import_result = MagicMock()
        mock_import_result.count = 0
        mock_gpg.import_keys.return_value = mock_import_result

        out = StringIO()
        call_command('import_pgp_private_key', self.key_path, stdout=out)

        self.assertIn('Failed to import key', out.getvalue())
        self.assertEqual(PGPSigningKey.objects.count(), 0,
                         "No key should be created when import fails")
