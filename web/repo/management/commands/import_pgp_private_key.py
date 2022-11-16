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

from django.core.management.base import BaseCommand, CommandError
from repo.models import PGPSigningKey
import gnupg
import os

class Command(BaseCommand):
    help = 'Ensures that all PGP keys in database are added to local keychain'

    def add_arguments(self, parser):
        parser.add_argument('private_key_path', type=str, help='Path to GPG private key stored in PEM format')

    def handle(self, *args, **options):

        if not os.path.isfile(options['private_key_path']):
            self.stdout.write(f"Cannot find file {options['private_key_path']}")
            return

        gpg = gnupg.GPG()
        gpg.encoding = 'utf-8'

        import_result = gpg.import_keys_file(options['private_key_path'])

        self.stdout.write(self.style.SUCCESS('Successfully imported key'))
