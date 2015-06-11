from collections import namedtuple

import mock

from test.TestHelper import MockFsHelper
from test.test_mock_torrent_file import MockTorrentFile
from recovery2 import Generator

__author__ = 'szyszy'

import unittest


class MyTestCase(unittest.TestCase):

    @mock.patch('FileFinder.os')
    def setUp(self, mock_os):
        self.PathAndLength = namedtuple('PathAndLength', 'path length')

        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(123454)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(123455)
        self.mock_fs_helper.cache_in_filefinder()

    @mock.patch('FileFinder.os')
    def test_determine_offsets_skip_only_the_first_file(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(123454)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(123455)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1.nfo', 'c.c1.f2.txt']).end(12)
        self.mock_fs_helper.cache_in_filefinder()
        paths = [self.PathAndLength('shouldskip1.txt', 123), self.PathAndLength('path2', 123454), self.PathAndLength('path3', 123455)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)
        self.assertEqual(1, len(generator.offsets))
        self.assertEqual((0, 123), generator.offsets[0])


    @mock.patch('FileFinder.os')
    def test_determine_offsets_skip_multiple_files(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(125000)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(135000)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1.nfo', 'c.c1.f2.txt']).end(12)
        self.mock_fs_helper.cache_in_filefinder()
        paths = [self.PathAndLength('shouldskip1.txt', 122), self.PathAndLength('path2', 125000),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)
        offset2_start = 122 + 125000
        offset3_start = 122 + 125000 + 123 + 135000
        self.assertEqual(3, len(generator.offsets))
        self.assertEqual((0, 122), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 123), generator.offsets[1])
        self.assertEqual((offset3_start, offset3_start + 124), generator.offsets[2])

    @mock.patch('FileFinder.os')
    def test_determine_offsets_offset_consecutive_skip_count_as_one_offset(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(125000)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(135000)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1.nfo', 'c.c1.f2.txt']).end(12)
        self.mock_fs_helper.cache_in_filefinder()
        paths = [self.PathAndLength('shouldskip1.txt', 122),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)
        offset2_start = 122 + 123 + 135000
        self.assertEqual(2, len(generator.offsets))
        self.assertEqual((0, 122 + 123), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 124), generator.offsets[1])

    @mock.patch('FileFinder.os')
    def test_determine_offsets_skip_multiple_files_and_last_file_if_no_candidates_found(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(125000)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(135000)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1.nfo', 'c.c1.f2.txt']).end(12)
        self.mock_fs_helper.cache_in_filefinder()
        paths = [self.PathAndLength('shouldskip1.txt', 122), self.PathAndLength('path2', 125000),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124), self.PathAndLength('shouldskip4.mp3', 23456)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)
        offset2_start = 122 + 125000
        offset3_start = 122 + 125000 + 123 + 135000
        offset3_end = offset3_start + 124 + 23456
        self.assertEqual(3, len(generator.offsets))
        self.assertEqual((0, 122), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 123), generator.offsets[1])
        self.assertEqual((offset3_start, offset3_end), generator.offsets[2])