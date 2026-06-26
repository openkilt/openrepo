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

import logging
import os

from django.conf import settings

from .base_repo import BaseRepoAdapter

logger = logging.getLogger("openrepo_web")


# Repo config looks like:
# deb [arch=amd64 signed-by=/key.gpg2] http://172.17.0.1:9000/mytestrepo/amd64 stable mains

DEB_ARCH_NAME = "any"


class DebRepoAdapter(BaseRepoAdapter):

    def _get_repo_instructions(self):
        dest_gpg_path = f"/usr/share/keyrings/openrepo-{self.repo_uid}.gpg"

        repo_address = "apt update && apt install -y curl gnupg\n"
        repo_address += f"curl {self.base_url}/public.gpg | gpg --yes --dearmor -o {dest_gpg_path}\n"
        repo_address += f'echo "deb [arch={DEB_ARCH_NAME} signed-by={dest_gpg_path}] {self.base_url}/ stable main" > /etc/apt/sources.list.d/openrepo-{self.repo_uid}.list\n'
        repo_address += "apt update"
        return repo_address

    def _generate_repo_structure(self, repo_path):

        # poolnames = ['main', 'contrib', 'non-free']
        poolnames = ["main"]

        directories = []
        for poolname in poolnames:
            directories.append(f"pool/{poolname}")
            directories.append(f"dists/stable/{poolname}/binary-{DEB_ARCH_NAME}")

        for dirpath in directories:
            fullpath = os.path.join(repo_path, dirpath)
            with self._buildlog_section(f"Creating directory {fullpath}"):
                os.makedirs(fullpath, exist_ok=True)

        all_pools = " ".join(poolnames)
        release_conf = 'APT::FTPArchive::Release::Codename "stable";' + "\n"
        release_conf += f'APT::FTPArchive::Release::Components "{all_pools}";' + "\n"
        release_conf += f'APT::FTPArchive::Release::Label "{self.repo_uid} APT Repository";' + "\n"
        release_conf += f'APT::FTPArchive::Release::Architectures "{DEB_ARCH_NAME}";'

        with self._buildlog_section("Writing release.conf"):
            release_conf_path = os.path.join(repo_path, "release.conf")
            with open(release_conf_path, "w+") as f:
                f.writelines(release_conf)

        # Symlink all files in the repo
        package_dest = os.path.join(repo_path, "pool/main/")
        self._copy_packages(package_dest)

        exec_commands = []

        aptftp_options = f"--db {settings.DEB_DB_PATH} -o APT::FTPArchive::AlwaysStat=true"
        for poolname in poolnames:
            exec_commands.append(
                f"apt-ftparchive {aptftp_options} packages pool/ > dists/stable/{poolname}/binary-{DEB_ARCH_NAME}/Packages"
            )
            exec_commands.append(f"gzip -k dists/stable/{poolname}/binary-{DEB_ARCH_NAME}/Packages")

        for poolname in poolnames:
            exec_commands.append(
                f"apt-ftparchive {aptftp_options} contents pool/{poolname} > dists/stable/{poolname}/Contents-{DEB_ARCH_NAME}"
            )
            exec_commands.append(f"gzip -k dists/stable/{poolname}/Contents-{DEB_ARCH_NAME}")

        for poolname in poolnames:
            exec_commands.append(
                f"apt-ftparchive {aptftp_options} release dists/stable/{poolname}/binary-{DEB_ARCH_NAME} > dists/stable/{poolname}/binary-{DEB_ARCH_NAME}/Release"
            )

        exec_commands.append(
            f"apt-ftparchive {aptftp_options} release -c release.conf dists/stable > dists/stable/Release"
        )

        if self.pgp_key is None:
            self._buildlog_write(
                "Missing PGP Key",
                "PGP key not configured for this repo.  Signing disabled",
                loglevel=self.BUILDLOG_WARNING,
            )
        else:
            exec_commands.append(
                f"gpg -a --yes --output dists/stable/Release.gpg --local-user {self.pgp_key.fingerprint} --detach-sign dists/stable/Release"
            )
            exec_commands.append(
                f"gpg -a --yes --clearsign --output dists/stable/InRelease --local-user {self.pgp_key.fingerprint} --detach-sign dists/stable/Release"
            )

            self._save_public_key(repo_path)

        return self._execute_commands(exec_commands, repo_path)
