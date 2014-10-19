from unittest import TestCase
from FileFinder import FileFinder
from test_mock_file_fs import Tree
import mock
from mock import MagicMock
from mock import Mock
from mock import PropertyMock
from mock import patch
from test_mock_file_fs import Helper
from test_mock_file_fs import MockFs
from test_mock_file_fs import MockOsHelper
import os

__author__ = 'szyszy'


class TestFileFinder(TestCase):

    @mock.patch('FileFinder.os')
    def test_cache_files_by_size(self, mock_os):
        fs = MockFs()
        MockOsHelper.init(fs, mock_os)

        dirs = MagicMock()
        dirs.__iter__.return_value = fs.get_top_level_dirs()

        filefinder = FileFinder()
        filefinder.cache_files_by_size(dirs)

        self.assertDictEqual(fs.get_last_random_sizes_dict(), filefinder.files_by_size)

    @mock.patch('FileFinder.os')
    def test_cache_files_by_size_differentiates_two_same_named_subfolders(self, mock_os):
        fs = MockFs(add_defaults=False)
        MockOsHelper.init(fs, mock_os)

        fs.add_dir('a').add_dir('b1').add_files(['a.b1.f1']).end()
        fs.add_dir('a').add_dir('b1').add_files(['a.b1.f1']).end()

        dirs = MagicMock()
        dirs.__iter__.return_value = fs.get_top_level_dirs()

        filefinder = FileFinder()
        filefinder.cache_files_by_size(dirs)

        self.assertDictEqual(fs.get_last_random_sizes_dict(), filefinder.files_by_size)
