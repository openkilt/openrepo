# Copyright 2022 by Open Kilt LLC. All rights reserved.
from django.test import TestCase
from repo.models import Repository, Package, PGPSigningKey
from django.conf import settings
import os
from unittest.mock import patch, MagicMock
import datetime
import pytz

class SignalTestCase(TestCase):
    def setUp(self):
        self.signing_key = PGPSigningKey.objects.create(
            name="Test Key",
            email="test@example.com",
            fingerprint="ABCDEF1234567890",
            public_key_pem="dummy public",
            private_key_pem="dummy private"
        )
        self.repo = Repository.objects.create(
            repo_uid="test-repo",
            repo_type='deb',
            signing_key=self.signing_key
        )
        self.repo2 = Repository.objects.create(
            repo_uid="test-repo-2",
            repo_type='deb',
            signing_key=self.signing_key
        )
        
        settings.STORAGE_PATH = "/tmp/openrepo_signal_test"
        if not os.path.exists(settings.STORAGE_PATH):
            os.makedirs(settings.STORAGE_PATH)

    def test_repo_staleness_on_package_add(self):
        """Test that the repository is marked as stale when a package is added"""
        self.assertFalse(self.repo.is_stale)
        
        Package.objects.create(
            repo=self.repo,
            package_uid="pkg-1",
            filename="pkg1.deb",
            package_name="pkg1",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="abc"
        )
        
        self.repo.refresh_from_db()
        self.assertTrue(self.repo.is_stale)
        self.assertEqual(self.repo.package_count, 1)

    @patch('os.remove')
    @patch('os.path.isfile')
    def test_deduplication_file_deletion(self, mock_isfile, mock_remove):
        """Test that the physical file is only deleted when the last package reference is gone"""
        mock_isfile.return_value = True
        
        # Create two package entries (different repos) pointing to the same file (package_uid)
        pkg_uid = "shared-pkg-file"
        p1 = Package.objects.create(
            repo=self.repo,
            package_uid=pkg_uid,
            filename="pkg.deb",
            package_name="pkg",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="shared-hash"
        )
        
        p2 = Package.objects.create(
            repo=self.repo2,
            package_uid=pkg_uid,
            filename="pkg.deb",
            package_name="pkg",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="shared-hash"
        )
        
        # Delete the first package reference
        p1.delete()
        
        # File should NOT be deleted because p2 still exists
        self.assertFalse(mock_remove.called)
        
        # Delete the second package reference
        p2.delete()
        
        # Now it should be deleted
        self.assertTrue(mock_remove.called)
        # Verify the path (relative_path replaces - with /)
        expected_path = os.path.join(settings.STORAGE_PATH, "shared/pkg/file")
        mock_remove.assert_called_with(expected_path)

    def test_repo_staleness_on_package_delete(self):
        """Test that the repository is marked as stale when a package is removed"""
        pkg = Package.objects.create(
            repo=self.repo,
            package_uid="pkg-delete",
            filename="pkg.deb",
            package_name="pkg",
            version="1.0",
            architecture="all",
            upload_date=datetime.datetime.now(tz=pytz.utc),
            checksum_sha512="abc"
        )
        
        # Reset stale flag (set by the create signal)
        self.repo.is_stale = False
        self.repo.save()
        
        pkg.delete()
        
        self.repo.refresh_from_db()
        self.assertTrue(self.repo.is_stale)
        self.assertEqual(self.repo.package_count, 0)
