__author__ = 'szyszy'
import unittest
from recovery2 import TorrentRecovery
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
from recovery2 import Generator
from test_mock_torrent_file import MockTorrentFile
from collections import namedtuple
from TestHelper import MockFsHelper

class TestTorrentRecovery(unittest.TestCase):
    def setUp(self):
        parser = TorrentRecovery.setup_parser()
        self.args_dict = TorrentRecovery.create_args_dict(parser)

        ###open_torrentfile tests
        ## testcase: skip the loop if torrent corrupted
        ## testcase: seeks back to last file pos if piece_hash doesn't match

        ###GENERATOR, determine offsets tests
        ## testcase: if 2 consecutive unwanted files present,
        # the end marker should be the sum of the 2 lengths
        ## testcase: if 2 consecutive unwanted files present and nothing else,
        # the offsets are stored (it shouldnt work with the current code)
        ## testcase: test running sum calculated correctly, incremented every time it's needed
        ## testcase: only 2 file, second is unwanted, what happens?
        ## testcase: only 1 file, unwanted, doesn't skipped from offsets (last if checks this)

        ###GENERATOR, pieces_generator
        ## TC: do not process skippable files,
        #check that the next valid file's hash compared to the right portion of hash
        #pieces should seek with sum of length of the skipped files

        ## TC: given one file without any valid candidates
        # compute seek should be called -->last number of skipped pieces should be set to ???
        # actual pos should be incremented with length
        # last file marker should be incremented with length
        ## TC: self.new_candidate sets to true on every new candidate
        ## TC: if candidate is corrupted and it is the last candidate, self.torrent_corrupted sets to true
        ## TC: if candidate is corrupted and it is the last candidate, self.torrent_corrupted sets to false
        #self.actual_pos should contain the value of self.last_file_marker
    ## TC: always compute seek while processing candidates
    ## TC: storing last valid file piece in case of we're at the end of the file

    #def test_does_not_process_files_should_skip(self):


    ###GENERATOR, find_candidates_for_all_files:
    ## testcase: skips the unwanted extensions
    ## testcase: test whether candidates put under the correct key
    ## testcase: single torrent case, candidates are searched

    @mock.patch('FileFinder.os')
    def setUp(self, mock_os):
        self.PathAndLength = namedtuple('PathAndLength', 'path length')

        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(123454)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(123455)
        self.mock_fs_helper.cache_in_filefinder()

    def test_find_candidates_for_all_files(self):
        paths = [self.PathAndLength('path1', 123454), self.PathAndLength('path2', 123455)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)
        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)

        self.assertEqual(2, len(generator.candidates.keys()))
        self.assertListEqual([os.path.join('a', 'b1', 'a.b1.f1'), os.path.join('a', 'b1', 'a.b1.f2')], generator.candidates['path1'])
        self.assertListEqual([os.path.join('b', 'b1', 'a.b1.f1')], generator.candidates['path2'])

    @mock.patch('FileFinder.os')
    def test_find_candidates_for_all_files_skips_unwanted_exts(self, mock_os):
        self.mock_fs_helper = MockFsHelper(mock_os)
        self.mock_fs_helper.add_dir('a').add_dir('b1').add_files(['a.b1.f1', 'a.b1.f2']).end(123454)
        self.mock_fs_helper.add_dir('b').add_dir('b1').add_files(['a.b1.f1']).end(123455)
        self.mock_fs_helper.add_dir('c').add_dir('c1').add_files(['c.c1.f1.nfo', 'c.c1.f2.txt']).end(12)
        self.mock_fs_helper.cache_in_filefinder()

        paths = [self.PathAndLength('path1', 123454), self.PathAndLength('path2', 123455), self.PathAndLength('path.txt',12), self.PathAndLength('path.nfo', 12)]
        mock_torrent = MockTorrentFile('name', paths, 1234567)

        generator = Generator(mock_torrent.meta_info, self.mock_fs_helper.filefinder, None, None)

        self.assertEqual(2, len(generator.candidates.keys()))
        self.assertListEqual([os.path.join('a', 'b1', 'a.b1.f1'), os.path.join('a', 'b1', 'a.b1.f2')], generator.candidates['path1'])
        self.assertListEqual([os.path.join('b', 'b1', 'a.b1.f1')], generator.candidates['path2'])
