from .base_repo import BaseRepoAdapter
from django.conf import settings


class GenericRepoAdapter(BaseRepoAdapter):
    def _get_repo_instructions(self):
        base_url = f'http://{settings.DOMAIN_NAME}/{self.repo_uid}/'
        return f'{base_url}'


    def _generate_repo_structure(self, repo_path):

        # Symlink all files in the repo
        self._copy_packages(repo_path)

        # TODO:
        # 1. Build a single-page HTML that lists all files with attributes and is searchable via JS
        # 2. Sign the index file with PGP key
        # 3. Write the PGP key to the directory
        # 4. Write a .md5 file for each generic file in the repo containing the MD5 hash

        return True