import pytz
import rest_framework.exceptions
from django.contrib.auth.models import User
from rest_framework import viewsets
from datetime import datetime
from rest_framework.response import Response
from .filters import BuildFilter, BuildLogFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import UserSerializer, RepoSummarySerializer, \
                        PackageSummarySerializer, RepoDetailSerializer, PackageDetailSerializer, \
                        UploadSerializer, PGPKeySerializer, CopySerializer, BuildSerializer, BuildLogSerializer
from repo.storage.filemanager import RepoFileManager
from repo.storage.keyring import PGPKeyring
from adapters.file import create_adapter
from repo.models import Package, Repository, PGPSigningKey, Build, BuildLogLine
from django.conf import settings
from django.core.validators import validate_email
from .util import MultipleFieldLookupMixin, reduce_to_uid, compute_sha512
import os
import logging

logger = logging.getLogger("openrepo_web")

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class ReposViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    lookup_field = 'repo_uid'
    queryset = Repository.objects.all().order_by('repo_uid')
    serializer_class = RepoSummarySerializer

    def get_serializer_class(self):
        # On create, we want to provide more details than on the list retrieve
        if self.action == 'create':
            return RepoDetailSerializer
        return RepoSummarySerializer

    def perform_create(self, serializer):

        repo = serializer.save()

        # Create the repo on disk


class PGPKeysViewSet(viewsets.ModelViewSet):

    queryset = PGPSigningKey.objects.all().order_by('-name')
    serializer_class = PGPKeySerializer

    lookup_field = 'fingerprint'

    def create(self, request, *args, **kwargs):

        full_name = request.POST.get('name')
        email = request.POST.get('email')

        if len(full_name) < 1 or len(full_name) > 1024:
            raise rest_framework.exceptions.ValidationError({'name': "Invalid name"})

        try:
            validate_email(email)
        except:
            raise rest_framework.exceptions.ValidationError({'email': "Invalid e-mail address"})

        keyring = PGPKeyring()

        new_key = keyring.generate_key(full_name, email)

        return Response(status=rest_framework.status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        keyring = PGPKeyring()
        keyring.delete(instance.fingerprint)

        self.perform_destroy(instance)
        return Response(status=rest_framework.status.HTTP_204_NO_CONTENT)

class WhoAmIViewSet(rest_framework.mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class RepoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    lookup_field = 'repo_uid'
    queryset = Repository.objects.all()
    serializer_class = RepoDetailSerializer

    def perform_update(self, serializer):
        original_object = self.get_object()  # or (the private attribute) serializer.instance
        changes = serializer.validated_data
        instance = serializer.save()

        # If they update the PGP key, mark the repo as stale so it's regenerated
        if original_object.signing_key != changes['signing_key']:
            logger.debug(f"PGP key changed, marking repo as stale")
            instance.is_stale = True
            instance.save()



class PackagesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    lookup_field = 'repo__repo_uid'
    queryset = Package.objects.all().order_by('-filename')
    serializer_class = PackageSummarySerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        repo_uid = self.kwargs['repo_uid']
        return Package.objects.filter(repo__repo_uid=repo_uid)

class PackageViewSet(MultipleFieldLookupMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    lookup_fields = ('repo__repo_uid', 'package_uid')
    queryset = Package.objects.all()
    serializer_class = PackageDetailSerializer



class BuildViewSet(rest_framework.mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Build.objects.all()
    serializer_class = BuildSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = BuildFilter



class BuildLogViewSet(rest_framework.mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    # lookup_fields = ('repo__repo_uid', 'package_uid')
    queryset = BuildLogLine.objects.all()
    serializer_class = BuildLogSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = BuildLogFilter


# ViewSets define the view behavior.
class CopyViewSet(viewsets.ViewSet):
    serializer_class = CopySerializer

    def create(self, request, repo_uid, package_uid):
        src_repo = Repository.objects.get(repo_uid=repo_uid)
        package = Package.objects.get(repo=src_repo, package_uid=package_uid)

        dst_repo_uid = request.POST.get('dest_repo_uid')
        logger.debug(request.POST)
        logger.debug(f"Copying {repo_uid} / {package_uid} to {dst_repo_uid}")

        try:
            dst_repo = Repository.objects.get(repo_uid=dst_repo_uid)
        except Repository.DoesNotExist:
            raise rest_framework.exceptions.NotFound(f"Destination repo_uid {dst_repo_uid} not found")

        # Since DRF does not know that this "copy" is associated with a repo, we have to tell it explicitly
        # to check object permissions
        self.check_object_permissions(request, dst_repo)

        # Make sure destination repo is either the same type or is generic
        if dst_repo.repo_type != 'files' and dst_repo.repo_type != src_repo.repo_type:
            raise rest_framework.exceptions.ParseError(f"Incompatible destination repository.  Source repo is {src_repo.repo_type} "
                                                       f"destination repo is {dst_repo.repo_type}")

        # For generic repo, we always want to refer to the file by filename, not parsed package name
        if dst_repo.repo_type == 'files':
            package.package_name = package.filename

        if Package.objects.filter(repo=dst_repo, package_name=package.package_name, version=package.version).count() > 0:
            raise rest_framework.exceptions.ParseError(f"Package {package.package_name} v{package.version} already exists in destination repo {dst_repo}")

        if Package.objects.filter(repo=dst_repo, package_uid=package.package_uid):
            raise rest_framework.exceptions.ParseError(f"An identical package already exists in the destination repo {package.package_uid}")


        # Set "pk" to none in order to make the save create a new model
        # Thus copying it from one to another
        package.pk = None
        package.repo = dst_repo
        package.save()

        serializer = PackageDetailSerializer(package)
        response = serializer.data

        return Response(response)

# ViewSets define the view behavior.
class UploadViewSet(viewsets.ViewSet):
    serializer_class = UploadSerializer

    # def list(self, request):
    #     return Response("GET API")

    def create(self, request, repo_uid):
        repo = Repository.objects.get(repo_uid=repo_uid)

        # Since DRF does not know that this "create" is associated with a repo, we have to tell it explicitly
        # to check object permissions
        self.check_object_permissions(request, repo)

        file_uploaded = request.FILES.get('package_file')
        overwrite_str = request.POST.get('overwrite', '0').lower()
        if overwrite_str == 'true' or overwrite_str == '1' or overwrite_str == 'yes':
            overwrite = True
        else:
            overwrite = False

        #print(vars(file_uploaded))
        filesize = file_uploaded.size
        filename = file_uploaded.name

        file_manager = RepoFileManager()
        stored_filename = file_manager.get_filepath()
        full_stored_filepath = os.path.join(settings.STORAGE_PATH, stored_filename)

        with open(full_stored_filepath, 'wb') as outf:
            logger.debug(f"Writing file to {full_stored_filepath}")
            for chunk in file_uploaded.chunks():
                outf.write(chunk)

        try:
            file_info_adapter = create_adapter(repo.repo_type, full_stored_filepath, filename)

            if file_info_adapter is None:
                raise rest_framework.exceptions.ParseError("Error determining file type from repo")
        except:
            os.remove(full_stored_filepath)
            raise rest_framework.exceptions.ParseError("Error processing uploaded file")

        if Package.objects.filter(repo=repo, package_name=file_info_adapter.get_name(),
                                  version=file_info_adapter.get_version()).count() > 0:

            if overwrite:
                Package.objects.get(repo=repo, package_name=file_info_adapter.get_name(),
                                  version=file_info_adapter.get_version()).delete()
            else:
                raise rest_framework.exceptions.ParseError(f"Package {file_info_adapter.get_name()} version {file_info_adapter.get_version()} "
                                                       f"already exists in destination repo {repo_uid} and 'overwrite' is not specified")

        # Check if this package (with the same checksum) has already been uploaded in another repo.  If so,
        # copy the entry rather than save a new file
        sha512 = compute_sha512(full_stored_filepath)
        existing_pkg = Package.objects.filter(checksum_sha512=sha512).exclude(repo=repo).all()
        if len(existing_pkg) > 0:
            package = existing_pkg[0]
            logger.debug(f"Copying existing entry {package.package_uid}")
            package.pk = None
            os.unlink(full_stored_filepath)
        else:
            package = Package()
            package.package_uid = stored_filename.replace("/", "-")

        package.repo = repo
        package.upload_date = datetime.now(tz=pytz.utc)
        package.filename = filename
        package.build_date = file_info_adapter.get_builddate()
        package.architecture = file_info_adapter.get_architecture()
        package.version = file_info_adapter.get_version()
        package.package_name = file_info_adapter.get_name()
        package.checksum_sha512 = sha512
        package.save()

        serializer = PackageDetailSerializer(package)
        response = serializer.data
        # TODO: Process the file here and respond with the new package info via the package serializer
        #response = f"POST API {repo_uid} and you have uploaded a {content_type} file"
        return Response(response)

