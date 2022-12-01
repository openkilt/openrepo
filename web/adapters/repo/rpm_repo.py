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

from .base_repo import BaseRepoAdapter
from django.conf import settings
import os

class RpmRepoAdapter(BaseRepoAdapter):
    def _get_repo_instructions(self):
        repo_cfg_file = f'/etc/yum.repos.d/{self.repo_uid}.repo'
        repo_instr = f'echo """\n'
        repo_instr += f'[{self.repo_uid}]\n'
        repo_instr += f'name={self.repo_uid}\n'
        repo_instr += f'baseurl={self.base_url}\n'
        repo_instr += f'enabled=1\n'
        repo_instr += f'repo_gpgcheck=1\n'
        repo_instr += f'gpgkey={self.base_url}/public.gpg\n'
        repo_instr += f'""" > {repo_cfg_file}'

        return repo_instr


    def _generate_repo_structure(self, repo_path):


        # Symlink all files in the repo
        self._copy_packages(repo_path)

        # createrepo caches MD5 sums for files it has already seen
        # This saves significant time on regenerating the repo
        if not os.path.isdir(settings.RPM_CACHE_DIR):
            os.makedirs(settings.RPM_CACHE_DIR)

        exec_commands = [
            f'createrepo --cachedir {settings.RPM_CACHE_DIR} {repo_path}',
        ]

        if self.pgp_key is None:
            self._buildlog_write("Missing PGP Key", f"PGP key not configured for this repo.  Signing disabled", loglevel=self.BUILDLOG_WARNING )
        else:
            exec_commands.append(f'gpg --detach-sign --yes --local-user {self.pgp_key.fingerprint} --armor {repo_path}/repodata/repomd.xml')

            self._save_public_key(repo_path)


        return self._execute_commands(exec_commands, repo_path)