from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from repo.models import Repository, Package
from .serializers import PackageDetailSerializer
import logging

logger = logging.getLogger("openrepo_web")

class CustomOpenRepoPermission(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):

        logger.debug(f"Global permission test for {request.user.username} / {view.__class__.__name__}")

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        # Write permissions are only allowed to those with repository write access.
        # We need to pass through here for cases where the user could have write access (e.g., uploading a package,
        # or copying a package).  The following is brittle, it compares the string name of the class with a list,
        # but I couldn't find a simple way of type checking and avoiding circular imports
        pass_through_views = ['UploadViewSet', 'CopyViewSet', 'RepoViewSet', 'PackageViewSet']
        if view.__class__.__name__ in pass_through_views:
            # A user *could* have write permission here, so pass through this check
            # If they don't have write permission on a particular repo, it will fail the "has_object_permission" check
            return bool(request.user and request.user.is_authenticated)

        # Fallback, any other writes we'll only allow the superuser to perform
        return request.user.is_superuser


    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """

        logger.debug(f"Object permission test for {request.user.username} / {view.__class__.__name__} obj {obj.__class__.__name__}")
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            logger.debug("Safe method.  Proceed")
            return True

        # Any writes we'll allow the superuser to perform
        if request.user.is_superuser:
            return True

        # For non superusers, write permissions are only allowed to those with repository write access.
        if isinstance(obj, Repository):
            logger.debug(f"Repository write attempt by {request.user.username} on {obj.repo_uid}")
            return self._check_perm(request.user, obj)
        elif isinstance(obj, Package):
            logger.debug(f"Package write attempt by {request.user.username} on repo {obj.repo.repo_uid} for pkg {obj.package_uid}")
            return self._check_perm(request.user, obj.repo)


        logger.debug(f"Obj Access denied for user {request.user} -- view: {view.__class__.__name__} obj: {obj.__class__.__name__}")
        return False

    def _check_perm(self, user, repo):
        user_permissions = Repository.objects.filter(id=repo.pk, write_access=user)
        if len(user_permissions) > 0:
            return True

        logger.debug(f"User {user.username} unauthorized for {repo.repo_uid}")
        return False

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening