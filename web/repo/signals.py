import pytz
from django.db.models.signals import post_delete
from .models import Package
from django.dispatch import receiver
import datetime
from .storage.filemanager import RepoFileManager
from django.db.models import signals
import logging
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User

logger = logging.getLogger("openrepo_web")


@receiver(signals.post_delete, sender=Package)
def remove_unreferenced_packages(sender, instance, using, **kwargs):
    """
    Whenever a package is deleted, check if any other packages with this UID remain.
    IF not, delete the physical file from disk.
    """
    other_packages_count = Package.objects.filter(package_uid=instance.package_uid).count()

    if other_packages_count > 0:
        logger.debug(f"On delete, file remains because there are {other_packages_count} references")
    else:
        # This was the last one.  Delete the file
        file_manager = RepoFileManager()
        file_manager.delete(instance.relative_path())


@receiver([signals.post_save, signals.post_delete], sender=Package)
def flag_repo_as_stale(sender, instance, using, **kwargs):
    # Whenever a package has been added or removed from a repo, flag the repo as stale
    # so that the on-disk metadata can be regenerated.
    repo = instance.repo
    repo.is_stale = True

    # Update package count with number of referenced packages
    pkg_count = Package.objects.filter(repo=repo).count()
    repo.package_count = pkg_count

    # Update the modification date
    repo.last_updated = datetime.datetime.now(tz=pytz.utc)
    repo.save()

@receiver(signals.post_save, sender=User)
def create_auth_token(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    # When a new user is created, automatically generate a REST API token for authentication
    if created:
        user = instance
        new_token = Token()
        new_token.user = user
        new_token.save()