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
        input_data = self.gpg.gen_key_input(key_type="RSA",
                                       key_length=4096,
                                       expire_date="50y",
                                       name_real=full_name,
                                       name_email=email,
                                       no_protection=True)
        key = self.gpg.gen_key(input_data)

        fingerprint = key.fingerprint
        ascii_armored_public_keys = self.gpg.export_keys([fingerprint], secret=False)
        ascii_armored_private_keys = self.gpg.export_keys([fingerprint], secret=True, passphrase='')

        new_key = PGPSigningKey()
        new_key.name = full_name
        new_key.email = email
        new_key.public_key_pem = ascii_armored_public_keys
        new_key.private_key_pem = ascii_armored_private_keys
        new_key.fingerprint = fingerprint
        new_key.save()

        return new_key

    def delete(self, fingerprint):
        # Delete private key
        self.gpg.delete_keys(fingerprint, secret=True, passphrase='')
        # Delete public key
        self.gpg.delete_keys(fingerprint, secret=False)


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
            self.gpg.import_keys(pgp_key.private_key_pem)
            self.gpg.trust_keys(pgp_key.fingerprint, 'TRUST_ULTIMATE')
        #pass

    def detach_sign_file(self, pgp_key, output_file, input_file, clear_sign=False):
        with open(input_file, 'r') as inf:
            output_content = self.gpg.sign_file(inf, detach=True, keyid=pgp_key.fingerprint,
                                                clearsign=clear_sign, binary=False,
                                                output=output_file, extra_args=['-a'])

        #with open(output_file, 'w') as outf:
        #    outf.write(str(output_content))