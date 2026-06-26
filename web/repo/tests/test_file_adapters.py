# Copyright 2022 by Open Kilt LLC. All rights reserved.
import os

from django.test import TestCase

from adapters.file.file_adapter import GenericFileAdapter


class GenericFileAdapterTestCase(TestCase):
    def test_get_name_returns_filename(self):
        """GenericFileAdapter.get_name returns the original filename"""
        adapter = GenericFileAdapter("/some/path/file.tar.gz", "myfile.tar.gz")
        self.assertEqual(adapter.get_name(), "myfile.tar.gz")

    def test_get_architecture_is_any(self):
        """GenericFileAdapter always reports 'any' architecture"""
        adapter = GenericFileAdapter("/path/f", "anything.zip")
        self.assertEqual(adapter.get_architecture(), "any")

    def test_get_description_is_empty(self):
        """GenericFileAdapter returns empty description"""
        adapter = GenericFileAdapter("/path/f", "file.bin")
        self.assertEqual(adapter.get_description(), "")

    def test_get_builddate_is_none(self):
        """GenericFileAdapter returns None build date"""
        adapter = GenericFileAdapter("/path/f", "file.bin")
        self.assertIsNone(adapter.get_builddate())

    def test_get_version_from_semver(self):
        """GenericFileAdapter extracts x.y.z from filename"""
        adapter = GenericFileAdapter("/path/f", "my-app-1.2.3.tar.gz")
        self.assertEqual(adapter.get_version(), "1.2.3")

    def test_get_version_first_semver_wins(self):
        """GenericFileAdapter picks the first x.y.z pattern"""
        adapter = GenericFileAdapter("/path/f", "app-1.0.0-beta-2.3.4.zip")
        self.assertEqual(adapter.get_version(), "1.0.0")

    def test_get_version_no_match_returns_empty(self):
        """GenericFileAdapter returns empty string when no semver found"""
        adapter = GenericFileAdapter("/path/f", "no-version-here.bin")
        self.assertEqual(adapter.get_version(), "")

    def test_get_version_partial_version_ignored(self):
        """GenericFileAdapter ignores x.y without z component"""
        adapter = GenericFileAdapter("/path/f", "app-1.2-release.zip")
        self.assertEqual(adapter.get_version(), "")

    def test_get_version_v_prefix_ignored(self):
        """GenericFileAdapter handles version without 'v' prefix"""
        adapter = GenericFileAdapter("/path/f", "tool-v2.5.1.tar.bz2")
        self.assertEqual(adapter.get_version(), "2.5.1")


class DebFileAdapterMetadataTestCase(TestCase):
    def test_real_deb_file(self):
        """DebFileAdapter reads metadata from real .deb file"""
        from adapters.file.deb_adapter import DebFileAdapter

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        deb_path = os.path.join(cur_dir, "unittest_files/hello-world_1.0.0_all.deb")
        adapter = DebFileAdapter(deb_path)

        self.assertEqual(adapter.get_name(), "hello-world")
        self.assertEqual(adapter.get_version(), "1.0.0")
        self.assertEqual(adapter.get_architecture(), "all")
        self.assertIsNone(adapter.get_builddate())
        self.assertIsInstance(adapter.get_description(), str)


class RpmFileAdapterTestCase(TestCase):
    def test_get_version_with_release(self):
        """RpmFileAdapter appends release to version when RPM_VERSION_IGNORE_BUILD_NUM=False"""
        from unittest.mock import MagicMock, patch

        from django.conf import settings

        with patch("rpmfile.open") as mock_rpm_open:
            mock_rpm = MagicMock()
            mock_rpm.headers.get.side_effect = lambda x: {
                "name": b"pkg",
                "version": b"2.0.0",
                "release": b"5",
                "arch": b"amd64",
                "buildtime": 1600000000,
                "description": b"desc",
                "group": None,
                "size": None,
                "copyright": None,
                "signature": None,
                "sourcerpm": None,
                "buildhost": None,
                "url": None,
                "summary": None,
            }.get(x)
            mock_rpm_open.return_value.__enter__.return_value = mock_rpm

            settings.RPM_VERSION_IGNORE_BUILD_NUM = False
            from adapters.file.rpm_adapter import RpmFileAdapter

            adapter = RpmFileAdapter("dummy.rpm")
            self.assertEqual(adapter.get_version(), "2.0.0.5")

    def test_get_version_ignore_release(self):
        """RpmFileAdapter returns only version when RPM_VERSION_IGNORE_BUILD_NUM=True"""
        from unittest.mock import MagicMock, patch

        from django.conf import settings

        with patch("rpmfile.open") as mock_rpm_open:
            mock_rpm = MagicMock()
            mock_rpm.headers.get.side_effect = lambda x: {
                "name": b"pkg",
                "version": b"2.0.0",
                "release": b"5",
                "arch": b"amd64",
                "buildtime": 1600000000,
                "description": b"desc",
                "group": None,
                "size": None,
                "copyright": None,
                "signature": None,
                "sourcerpm": None,
                "buildhost": None,
                "url": None,
                "summary": None,
            }.get(x)
            mock_rpm_open.return_value.__enter__.return_value = mock_rpm

            settings.RPM_VERSION_IGNORE_BUILD_NUM = True
            from adapters.file.rpm_adapter import RpmFileAdapter

            adapter = RpmFileAdapter("dummy.rpm")
            self.assertEqual(adapter.get_version(), "2.0.0")

    def test_get_architecture(self):
        """RpmFileAdapter extracts architecture"""
        from unittest.mock import MagicMock, patch

        from django.conf import settings

        with patch("rpmfile.open") as mock_rpm_open:
            mock_rpm = MagicMock()
            mock_rpm.headers.get.side_effect = lambda x: {
                "name": b"pkg",
                "version": b"1.0",
                "release": b"1",
                "arch": b"x86_64",
                "buildtime": 1600000000,
                "description": b"desc",
                "group": None,
                "size": None,
                "copyright": None,
                "signature": None,
                "sourcerpm": None,
                "buildhost": None,
                "url": None,
                "summary": None,
            }.get(x)
            mock_rpm_open.return_value.__enter__.return_value = mock_rpm

            settings.RPM_VERSION_IGNORE_BUILD_NUM = False
            from adapters.file.rpm_adapter import RpmFileAdapter

            adapter = RpmFileAdapter("dummy.rpm")
            self.assertEqual(adapter.get_architecture(), "x86_64")
