from .deb_repo import DepRepoAdapter
from .rpm_repo import RpmRepoAdapter
from .generic_repo import GenericRepoAdapter

def get_repo_adapter(repo_obj):
    if repo_obj.repo_type == 'deb':
        return DepRepoAdapter(repo_obj)
    elif repo_obj.repo_type == 'rpm':
        return RpmRepoAdapter(repo_obj)
    elif repo_obj.repo_type == 'files':
        return GenericRepoAdapter(repo_obj)
    raise Exception("Not implemented")