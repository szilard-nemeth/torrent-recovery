from collections import namedtuple
from testfixtures import tempdir
from FileFinder import FileFinder
from test.testhelpers.test_mock_file import ContentManager
from test.testhelpers.test_mock_torrent_file import MockTorrentFile
from recovery2 import Generator

__author__ = 'szyszy'

import unittest


class TestFileOffset(unittest.TestCase):

    def setUp(self):
        self.PathAndLength = namedtuple('PathAndLength', 'path length')
        self.file_finder = FileFinder()

    @tempdir()
    def test_determine_offsets_skip_only_the_first_file(self, temp_dir):
        temp_dir.write('a/b1/a.b1.f1', ContentManager.generate_random_binary(123454).getvalue())
        temp_dir.write('a/b1/a.b1.f2', ContentManager.generate_random_binary(123454).getvalue())

        temp_dir.write('b/b1/b.b1.f1', ContentManager.generate_random_binary(123455).getvalue())

        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('shouldskip1.txt', 123),
                 self.PathAndLength('path2', 123454),
                 self.PathAndLength('path3', 123455)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.file_finder, None, None)
        self.assertEqual(1, len(generator.offsets))
        self.assertEqual((0, 123), generator.offsets[0])

    @tempdir()
    def test_determine_offsets_skip_multiple_files(self, temp_dir):
        temp_dir.write('a/b1/a.b1.f1', ContentManager.generate_random_binary(125000).getvalue())
        temp_dir.write('a/b1/a.b1.f2', ContentManager.generate_random_binary(125000).getvalue())

        temp_dir.write('b/b1/b.b1.f1', ContentManager.generate_random_binary(135000).getvalue())

        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('shouldskip1.txt', 122), self.PathAndLength('path2', 125000),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124)]

        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.file_finder, None, None)
        offset2_start = 122 + 125000
        offset3_start = 122 + 125000 + 123 + 135000
        self.assertEqual(3, len(generator.offsets))
        self.assertEqual((0, 122), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 123), generator.offsets[1])
        self.assertEqual((offset3_start, offset3_start + 124), generator.offsets[2])

    @tempdir()
    def test_determine_offsets_offset_consecutive_skip_count_as_one_offset(self, temp_dir):
        temp_dir.write('a/b1/a.b1.f1', ContentManager.generate_random_binary(125000).getvalue())
        temp_dir.write('a/b1/a.b1.f2', ContentManager.generate_random_binary(125000).getvalue())

        temp_dir.write('b/b1/b.b1.f1', ContentManager.generate_random_binary(135000).getvalue())

        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('shouldskip1.txt', 122),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124)]

        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.file_finder, None, None)
        offset2_start = 122 + 123 + 135000
        self.assertEqual(2, len(generator.offsets))
        self.assertEqual((0, 122 + 123), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 124), generator.offsets[1])

    @tempdir()
    def test_determine_offsets_skip_multiple_files_and_last_file_if_no_candidates_found(self, temp_dir):
        temp_dir.write('a/b1/a.b1.f1', ContentManager.generate_random_binary(125000).getvalue())
        temp_dir.write('a/b1/a.b1.f2', ContentManager.generate_random_binary(125000).getvalue())

        temp_dir.write('b/b1/b.b1.f1', ContentManager.generate_random_binary(135000).getvalue())

        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('shouldskip1.txt', 122), self.PathAndLength('path2', 125000),
                 self.PathAndLength('shouldskip2.jpg', 123), self.PathAndLength('path3', 135000),
                 self.PathAndLength('shouldskip3.nfo', 124), self.PathAndLength('shouldskip4.mp3', 23456)]

        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.file_finder, None, None)
        offset2_start = 122 + 125000
        offset3_start = 122 + 125000 + 123 + 135000
        offset3_end = offset3_start + 124 + 23456
        self.assertEqual(3, len(generator.offsets))
        self.assertEqual((0, 122), generator.offsets[0])
        self.assertEqual((offset2_start, offset2_start + 123), generator.offsets[1])
        self.assertEqual((offset3_start, offset3_end), generator.offsets[2])
