# Copyright 2022 by Open Kilt LLC. All rights reserved.
import os
import tempfile

from django.conf import settings
from django.test import TestCase

from repo.storage.filemanager import RepoFileManager


class FileManagerTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.STORAGE_PATH = self.test_dir
        settings.STORAGE_PREFIX_DEPTH = 2
        settings.STORAGE_FILENAME_LENGTH = 8

    def test_get_filepath_returns_string(self):
        """get_filepath returns a relative path string"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)

    def test_get_filepath_creates_directory(self):
        """get_filepath creates the subdirectory on disk"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        full_dir = os.path.dirname(os.path.join(settings.STORAGE_PATH, path))
        self.assertTrue(os.path.isdir(full_dir))

    def test_get_filepath_prefix_depth(self):
        """get_filepath respects STORAGE_PREFIX_DEPTH"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        parts = path.split(os.sep)
        # Should have exactly one prefix dir segment + filename
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), settings.STORAGE_PREFIX_DEPTH)

    def test_get_filepath_filename_length(self):
        """get_filepath respects STORAGE_FILENAME_LENGTH"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        filename = os.path.basename(path)
        self.assertEqual(len(filename), settings.STORAGE_FILENAME_LENGTH)

    def test_get_filepath_unique(self):
        """Two consecutive calls return different paths"""
        fm = RepoFileManager()
        path1 = fm.get_filepath()
        path2 = fm.get_filepath()
        self.assertNotEqual(path1, path2)

    def test_delete_existing_file(self):
        """delete() removes a file that exists"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        full_path = os.path.join(settings.STORAGE_PATH, path)
        with open(full_path, "w") as f:
            f.write("test")
        self.assertTrue(os.path.isfile(full_path))
        fm.delete(path)
        self.assertFalse(os.path.isfile(full_path))

    def test_delete_nonexistent_file_does_not_raise(self):
        """delete() on a non-existent path does not raise"""
        fm = RepoFileManager()
        fm.delete("nonexistent/file")  # should not raise

    def test_get_filepath_all_lowercase_alpha(self):
        """Generated paths contain only lowercase letters"""
        fm = RepoFileManager()
        path = fm.get_filepath()
        clean = path.replace(os.sep, "")
        self.assertTrue(clean.isalpha())
        self.assertEqual(clean, clean.lower())
