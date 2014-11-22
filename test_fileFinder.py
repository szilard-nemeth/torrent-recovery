import unittest
from FileFinder import FileFinder
from test_mock_file_fs import Tree
import mock
from mock import MagicMock
from mock import Mock
from mock import PropertyMock
from mock import patch
from test_mock_file_fs import Helper
from test_mock_file_fs import MockFs
from test_mock_file_fs import MockOs
import os

__author__ = 'szyszy'

from TestHelper import MockFsHelper
class TestFileFinder(unittest.TestCase):

    @mock.patch('FileFinder.os')
    def test_cache_files_by_size(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os, add_defaults=True)
        self.mock_fs_helper.cache_in_filefinder()

        self.assertDictEqual(self.mock_fs_helper.fs.get_last_sizes_dict(), self.mock_fs_helper.filefinder.files_by_size)

    @mock.patch('FileFinder.os')
    def test_cache_files_by_size_differentiates_two_same_named_subfolders(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1']).end(123456)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(123456)
        self.mock_fs_helper.cache_in_filefinder()

        self.assertDictEqual(self.mock_fs_helper.fs.get_last_sizes_dict(), self.mock_fs_helper.filefinder.files_by_size)

    @mock.patch('FileFinder.os')
    def test_find_candidate_files_from_cache(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)

        self.mock_fs_helper.add_dir('a').add_dir('a1').add_files(['a.a1.f1']).end(123456)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['b.b1.f1']).end(67890)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1', 'c.c1.f2']).end(333333)
        self.mock_fs_helper.cache_in_filefinder()

        filefinder = self.mock_fs_helper.filefinder
        self.assertListEqual([os.path.join('a', 'a1', 'a.a1.f1')], filefinder.find_candidate_files_matching_size_from_cache(123456))
        self.assertListEqual([os.path.join('b', 'b1', 'b.b1.f1')], filefinder.find_candidate_files_matching_size_from_cache(67890))
        self.assertListEqual([os.path.join('c', 'c1', 'c.c1.f1'), os.path.join('c', 'c1', 'c.c1.f2')], filefinder.find_candidate_files_matching_size_from_cache(333333))