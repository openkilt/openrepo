from .base_adapter import RepoFileAdapter
from .deb_adapter import DebFileAdapter
from .rpm_adapter import RpmFileAdapter
from .file_adapter import GenericFileAdapter
import logging

logger = logging.getLogger("openrepo_web")


def create_adapter(repo_type, filepath, original_filename):
    if repo_type == 'deb':
        return DebFileAdapter(filepath)
    elif repo_type == 'rpm':
        return RpmFileAdapter(filepath)
    elif repo_type == 'files':
        return GenericFileAdapter(filepath, original_filename)
    else:
        logger.warning(f"Unable to determine file adapter from repo type {repo_type}")
        return None