from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from repo.models import Repository, PGPSigningKey, Package
from rest_framework.authtoken.models import Token
import datetime


def _make_admin(username: str):
    User = get_user_model()
    User.objects.filter(username=username).delete()
    return User.objects.create_superuser(username=username, password='password123')


def _make_user(username: str):
    User = get_user_model()
    User.objects.filter(username=username).delete()
    return User.objects.create_user(username=username, password='password123')


def _make_key():
    return PGPSigningKey.objects.create(
        name="Test Key", email="test@example.com",
        fingerprint="ABCDEF1234567890",
        public_key_pem="dummy public", private_key_pem="dummy private",
    )


class CircularPromoteDetectionTest(APITestCase):
    """Tests for circular promote_to detection in RepoDetailSerializer"""

    def setUp(self):
        self.admin = _make_admin('circ-admin')
        self.token = Token.objects.get(user=self.admin).key
        self.auth = f'Token {self.token}'
        self.signing_key = _make_key()
        self.repo_a = Repository.objects.create(repo_uid='repo-a', repo_type='deb')
        self.repo_b = Repository.objects.create(repo_uid='repo-b', repo_type='deb')

    def test_linear_promote_chain_succeeds(self):
        response = self.client.put(
            f'/api/repo-a/',
            {'repo_uid': 'repo-a', 'repo_type': 'deb',
             'promote_to': 'repo-b', 'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=self.auth, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_circular_promote_direct(self):
        self.client.put(
            f'/api/repo-a/',
            {'repo_uid': 'repo-a', 'repo_type': 'deb',
             'promote_to': 'repo-b', 'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=self.auth, format='json',
        )
        response = self.client.put(
            f'/api/repo-b/',
            {'repo_uid': 'repo-b', 'repo_type': 'deb',
             'promote_to': 'repo-a', 'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=self.auth, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('promote_to', response.data)

    def test_multiple_repos_pointing_to_same_target(self):
        self.client.put(
            f'/api/repo-a/',
            {'repo_uid': 'repo-a', 'repo_type': 'deb',
             'promote_to': 'repo-b', 'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=self.auth, format='json',
        )
        repo_c = Repository.objects.create(repo_uid='repo-c', repo_type='deb')
        response = self.client.put(
            f'/api/repo-c/',
            {'repo_uid': 'repo-c', 'repo_type': 'deb',
             'promote_to': 'repo-b', 'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=self.auth, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SearchFilterPaginationTest(APITestCase):
    """Tests for search, filter, and pagination on PackagesViewSet"""

    def setUp(self):
        self.admin = _make_admin('search-admin')
        self.token = Token.objects.get(user=self.admin).key
        self.auth = f'Token {self.token}'

        self.repo = Repository.objects.create(repo_uid='test-repo', repo_type='deb')
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for i in range(15):
            Package.objects.create(
                repo=self.repo,
                package_uid=f'pkg-{i:03d}',
                filename=f'pkg-{i:03d}.deb',
                package_name=f'hello-{i}' if i < 10 else f'zebra-{i}',
                version=f'1.{i}.0',
                architecture='all',
                upload_date=now,
                checksum_sha512='dummy',
            )

    def test_search_by_package_name(self):
        response = self.client.get(
            '/api/test-repo/packages/?search=hello',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for pkg in response.data['results']:
            self.assertIn('hello', pkg['package_name'])

    def test_search_by_filename(self):
        response = self.client.get(
            '/api/test-repo/packages/?search=pkg-001',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_by_version(self):
        response = self.client.get(
            '/api/test-repo/packages/?search=1.5.0',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for pkg in response.data['results']:
            self.assertIn('1.5.0', pkg['version'])

    def test_pagination_default_page_size(self):
        response = self.client.get(
            '/api/test-repo/packages/',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 15)

    def test_pagination_custom_page_size(self):
        response = self.client.get(
            '/api/test-repo/packages/?page_size=5',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)

    def test_pagination_second_page(self):
        response = self.client.get(
            '/api/test-repo/packages/?page=2&page_size=5',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)

    def test_ordering_default_desc_upload_date(self):
        response = self.client.get(
            '/api/test-repo/packages/',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        dates = [r['upload_date'] for r in results]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_ordering_ascending(self):
        response = self.client.get(
            '/api/test-repo/packages/?ordering=package_name',
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        names = [r['package_name'] for r in results]
        self.assertEqual(names, sorted(names, key=str.lower))


class PermissionEdgeCaseTest(APITestCase):
    """Tests for write_access permission edge cases"""

    def setUp(self):
        self.admin = _make_admin('perm-admin')
        self.normie = _make_user('perm-normie')
        self.admin_token = Token.objects.get(user=self.admin).key
        self.normie_token = Token.objects.get(user=self.normie).key

        self.signing_key = _make_key()

        self.allowed_repo = Repository.objects.create(
            repo_uid='allowed-repo', repo_type='deb',
        )
        self.allowed_repo.write_access.add(self.normie)

        self.dest_repo = Repository.objects.create(
            repo_uid='dest-repo', repo_type='deb',
        )
        self.dest_repo.write_access.add(self.normie)

        self.restricted_repo = Repository.objects.create(
            repo_uid='restricted-repo', repo_type='deb',
        )

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        self.src_pkg = Package.objects.create(
            repo=self.allowed_repo,
            package_uid='src-pkg',
            filename='src.deb', package_name='src',
            version='1.0', architecture='all',
            upload_date=now, checksum_sha512='dummy',
        )

    def test_normie_can_copy_to_allowed_repo(self):
        response = self.client.post(
            f'/api/allowed-repo/pkg/{self.src_pkg.package_uid}/copy/',
            {'dest_repo_uid': 'dest-repo'},
            HTTP_AUTHORIZATION=f'Token {self.normie_token}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normie_cannot_copy_to_restricted_repo(self):
        response = self.client.post(
            f'/api/allowed-repo/pkg/{self.src_pkg.package_uid}/copy/',
            {'dest_repo_uid': 'restricted-repo'},
            HTTP_AUTHORIZATION=f'Token {self.normie_token}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normie_cannot_create_repo(self):
        response = self.client.post(
            '/api/repos/',
            {'repo_uid': 'normie-repo', 'repo_type': 'deb',
             'signing_key': self.signing_key.fingerprint},
            HTTP_AUTHORIZATION=f'Token {self.normie_token}', format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
