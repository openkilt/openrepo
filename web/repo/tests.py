from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Repository, Package
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.conf import settings

class RepoRestApiTestCase(APITestCase):
    def setUp(self):

        # print("SETTING UP")
        # setup authentication
        User = get_user_model()
        self.user = User.objects.create_user(username='matt',
                                        email='matt@test.com',
                                        password='4242424242')

        token = Token.objects.create(user=self.user)
        self.api_key = token.key

        self.http_auth = f'Token {self.api_key}'
        self.headers = {'Authorization': f'Token {self.api_key}'}

        settings.STORAGE_PATH = "/tmp/openrepo_test"

    def tearDown(self):
        pass
        #print("TEARING DOWN")

    def test_repo_create_delete(self):
        """Create, list, and delete a repo"""

        REPO_UID = 'test-repo'

        response = self.client.post('/api/repos/',
                                    {'repo_uid': REPO_UID,
                                     'repo_name': 'Test repo',
                                     'architecture': 'x86_64',
                                     'repo_type': 'deb'},
                                    HTTP_AUTHORIZATION=self.http_auth,  format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Repository.objects.count(), 1)
        self.assertEqual(Repository.objects.get().repo_uid, REPO_UID)

        response = self.client.delete(f'/api/{REPO_UID}/', HTTP_AUTHORIZATION=self.http_auth,  format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Repository.objects.count(), 0)

    def test_package_upload_delete(self):

        REPO_UID = 'pkgrepo'

        CUR_DIR = os.path.dirname(os.path.realpath(__file__))

        response = self.client.post('/api/repos/',
                                    {'repo_uid': REPO_UID,
                                     'repo_name': 'Test repo',
                                     'architecture': 'x86_64',
                                     'repo_type': 'deb'},
                                    HTTP_AUTHORIZATION=self.http_auth,  format='json')

        upload_file_path = os.path.join(CUR_DIR, 'unittest_files/hello-world_1.0.0_all.deb')
        with open(upload_file_path, 'rb') as upload_file_buffer:
            response = self.client.post(f'/api/{REPO_UID}/upload/',
                                        data={'package_file': upload_file_buffer}, format='multipart',
                                        HTTP_AUTHORIZATION=self.http_auth )

        package = Package.objects.get()
        disk_path = os.path.join(settings.STORAGE_PATH, package.package_uid.replace("-", "/"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Package.objects.count(), 1)
        self.assertTrue(os.path.isfile(disk_path))

        # Delete the package and make sure that the file on disk is deleted as well
        response = self.client.delete(f'/api/{REPO_UID}/pkg/{package.package_uid}/', HTTP_AUTHORIZATION=self.http_auth,  format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Package.objects.count(), 0)
        self.assertTrue(not os.path.isfile(disk_path))
