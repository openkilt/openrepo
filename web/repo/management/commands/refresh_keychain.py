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

from django.core.management.base import BaseCommand
from repo.models import PGPSigningKey
from repo.storage.keyring import PGPKeyring


class Command(BaseCommand):
    help = 'Import all PGP keys from the database into the local GPG keyring'

    def handle(self, *args, **options):
        keyring = PGPKeyring()
        keys = PGPSigningKey.objects.all()
        for key in keys:
            keyring.ensure_key(key)
        self.stdout.write(self.style.SUCCESS(f'Refreshed {keys.count()} PGP key(s) in keyring'))
