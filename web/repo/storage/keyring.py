# Copyright 2022 by Open Kilt LLC. All rights reserved.
# This file is part of the OpenRepo Repository Management Software (OpenRepo)
# OpenRepo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License
# version 3 as published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from django.conf import settings
import gnupg
from repo.models import PGPSigningKey
import os

class PGPKeyring:

    def __init__(self):
        if not os.path.isdir(settings.KEYRING_PATH):
            os.makedirs(settings.KEYRING_PATH)

        # Weird backport behavior with arguments
        # https://stackoverflow.com/questions/35028852/how-to-set-the-gnupg-home-directory-within-the-gnupg-python-binding
        try:
            self.gpg = gnupg.GPG(gnupghome=settings.KEYRING_PATH)
        except TypeError:
            self.gpg = gnupg.GPG(homedir=settings.KEYRING_PATH)

        self.gpg.encoding = 'utf-8'

    def generate_key(self, full_name, email):
        '''
        Creates a new PGP key and adds to the database
        :param full_name: Full name of user
        :param email: Full e-mail address of user
        :return: The newly created PGPSigningKey model object
        '''
        import subprocess as _sp
        import os as _os
        batch = _os.path.join(settings.KEYRING_PATH, 'keygen.batch')
        with open(batch, 'w') as _f:
            _f.write(
                'Key-Type: RSA\nKey-Length: 4096\n'
                f'Name-Real: {full_name}\n'
                f'Name-Email: {email}\n'
                'Expire-Date: 50y\n%no-protection\n%commit\n'
            )
        _sp.run(
            ['gpg', '--homedir', settings.KEYRING_PATH, '--batch', '--gen-key', batch],
            capture_output=True,
        )
        _os.unlink(batch)

        result = _sp.run(
            ['gpg', '--homedir', settings.KEYRING_PATH,
             '--list-secret-keys', '--with-colons'],
            capture_output=True, text=True,
        )
        fingerprint = None
        for line in result.stdout.splitlines():
            if line.startswith('fpr:'):
                fp = line.split(':')[9]
                fingerprint = fp

        ascii_armored_public_keys = _sp.run(
            ['gpg', '--homedir', settings.KEYRING_PATH, '--armor', '--export', fingerprint],
            capture_output=True,
        ).stdout
        ascii_armored_private_keys = _sp.run(
            ['gpg', '--homedir', settings.KEYRING_PATH, '--armor', '--export-secret-keys', fingerprint],
            capture_output=True,
        ).stdout

        new_key = PGPSigningKey()
        new_key.name = full_name
        new_key.email = email
        new_key.public_key_pem = ascii_armored_public_keys.decode()
        new_key.private_key_pem = ascii_armored_private_keys.decode()
        new_key.fingerprint = fingerprint
        new_key.save()

        return new_key

        new_key = PGPSigningKey()
        new_key.name = full_name
        new_key.email = email
        new_key.public_key_pem = ascii_armored_public_keys
        new_key.private_key_pem = ascii_armored_private_keys
        new_key.fingerprint = fingerprint
        new_key.save()

        return new_key

    def delete(self, fingerprint, passphrase=''):
        import subprocess as _sp
        # Delete keys via subprocess to avoid python-gnupg compatibility issues
        _sp.run(['gpg', '--homedir', settings.KEYRING_PATH, '--batch',
                 '--delete-secret-key', fingerprint],
                capture_output=True)
        _sp.run(['gpg', '--homedir', settings.KEYRING_PATH, '--batch',
                 '--delete-key', fingerprint],
                capture_output=True)


    def ensure_key(self, pgp_key):
        '''
        Ensures that the specified key is on the system keychain.  This is necessary so that
        CLI utilities are able to interact with the key
        :param fingerprint:
        '''

        public_keys = self.gpg.list_keys(False)

        found = False
        for key in public_keys:
            if pgp_key.fingerprint == key['fingerprint']:
                found = True
                break

        if not found:
            passphrase = pgp_key.passphrase if pgp_key.passphrase else None
            try:
                self.gpg.import_keys(pgp_key.private_key_pem, passphrase=passphrase)
            except TypeError:
                self.gpg.import_keys(pgp_key.private_key_pem)
            try:
                self.gpg.trust_keys(pgp_key.fingerprint, 'TRUST_ULTIMATE')
            except (AttributeError, TypeError):
                pass

    def detach_sign_file(self, pgp_key, output_file, input_file, clear_sign=False):
        import subprocess as _sp
        cmd = ['gpg', '--homedir', settings.KEYRING_PATH,
               '--local-user', pgp_key.fingerprint, '--armor',
               '--detach-sign', '--yes',
               '--output', output_file, input_file]
        if clear_sign:
            cmd = ['gpg', '--homedir', settings.KEYRING_PATH,
                   '--local-user', pgp_key.fingerprint, '--armor',
                   '--clearsign', '--yes',
                   '--output', output_file, input_file]
        _sp.run(cmd, capture_output=True)