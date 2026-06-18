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
from django.core.management import call_command
from repo.models import PGPSigningKey
from repo.storage.keyring import PGPKeyring

class Command(BaseCommand):
    help = 'Call before starting app server to ensure system is properly configured'

    def handle(self, *args, **options):
        call_command('refresh_keychain')

        self.stdout.write(self.style.SUCCESS('Completed startup checks'))
