import logging
import os
import pytz
from datetime import datetime
from django.db import close_old_connections
from django.conf import settings
from repo.models import UploadTask, Package
from adapters.file import create_adapter
from .serializers import PackageDetailSerializer
from .util import compute_sha512

logger = logging.getLogger("openrepo_web")


def process_upload(task_id):
    close_old_connections()

    try:
        task = UploadTask.objects.get(pk=task_id)
    except UploadTask.DoesNotExist:
        logger.error(f"UploadTask {task_id} not found for background processing")
        return

    task.status = 'processing'
    task.save(update_fields=['status'])

    repo = task.repo
    full_stored_filepath = task.stored_path
    filename = task.filename
    overwrite = task.overwrite

    try:
        file_info_adapter = create_adapter(repo.repo_type, full_stored_filepath, filename)

        if file_info_adapter is None:
            raise ValueError("Error determining file type from repo")

        if Package.objects.filter(repo=repo, package_name=file_info_adapter.get_name(),
                                  architecture=file_info_adapter.get_architecture(),
                                  version=file_info_adapter.get_version()).count() > 0:

            if overwrite:
                Package.objects.get(repo=repo, package_name=file_info_adapter.get_name(),
                                    architecture=file_info_adapter.get_architecture(),
                                    version=file_info_adapter.get_version()).delete()
            else:
                raise ValueError(f"Package {file_info_adapter.get_name()} version {file_info_adapter.get_version()} "
                                 f"already exists in destination repo {repo.repo_uid} and 'overwrite' is not specified")

        sha512 = compute_sha512(full_stored_filepath)
        existing_pkg = Package.objects.filter(checksum_sha512=sha512).exclude(repo=repo).all()
        if len(existing_pkg) > 0:
            package = existing_pkg[0]
            logger.debug(f"Copying existing entry {package.package_uid}")
            package.pk = None
            os.unlink(full_stored_filepath)
            stored_filename = None
        else:
            package = Package()
            stored_filename = os.path.relpath(full_stored_filepath, settings.STORAGE_PATH)
            package.package_uid = stored_filename.replace("/", "-")
            sha512 = compute_sha512(full_stored_filepath)

        package.repo = repo
        package.upload_date = datetime.now(tz=pytz.utc)
        package.filename = filename
        package.build_date = file_info_adapter.get_builddate()
        package.architecture = file_info_adapter.get_architecture()
        package.version = file_info_adapter.get_version()
        package.package_name = file_info_adapter.get_name()
        package.checksum_sha512 = sha512
        package.save()

        if repo.keep_only_latest:
            Package.objects.filter(repo=repo, package_name=package.package_name).exclude(pk=package.pk).delete()

        serializer = PackageDetailSerializer(package)
        task.result_data = serializer.data
        task.status = 'completed'
        task.completed_at = datetime.now(tz=pytz.utc)
        task.save(update_fields=['result_data', 'status', 'completed_at'])

    except Exception as e:
        logger.exception(f"Upload processing failed for task {task_id}")
        if os.path.exists(full_stored_filepath):
            try:
                os.remove(full_stored_filepath)
            except OSError:
                pass
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = datetime.now(tz=pytz.utc)
        task.save(update_fields=['status', 'error_message', 'completed_at'])
