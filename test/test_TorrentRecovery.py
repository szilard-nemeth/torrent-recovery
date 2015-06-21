import mock
from testfixtures import tempdir, TempDirectory

from FileFinder import FileFinder
from Generator import Generator
from test.testhelpers.content_manager import ContentManager


__author__ = 'szyszy'
import unittest
import os
from collections import namedtuple

from mock import patch

from recovery2 import TorrentRecovery
from test.testhelpers.mock_torrent_file import MockTorrentFile
import sys

PIECE_LENGTH = 125
DUMMY_DEST_DIR = 'dummy_dest_dir'
DUMMY_MEDIA_DIR = 'dummy_media_dir'


class TestTorrentRecovery(unittest.TestCase):
    def setUp(self):
        parser = TorrentRecovery.setup_parser()
        self.args_dict = TorrentRecovery.create_args_dict(parser)

        # ##open_torrentfile tests
        # # TC 1: skip the loop if torrent corrupted
        ## TC 2: seeks back to last file pos if piece_hash doesn't match
        ## TC 3: test running sum calculated correctly, incremented every time it's needed
        ## TC 4: only 2 file, second is unwanted, what happens?
        ## TC 5: only 1 file, unwanted, doesn't skipped from offsets (last if checks this)

        # ##GENERATOR, pieces_generator
        ## TC 6: do not process skippable files,
        #check that the next valid file's hash compared to the right portion of hash
        #pieces should seek with sum of length of the skipped files

        ## TC 7: given one file without any valid candidates
        # compute seek should be called -->last number of skipped pieces should be set to ???
        # actual pos should be incremented with length
        # last file marker should be incremented with length

        ## TC 8: self.new_candidate sets to true on every new candidate
        ## TC 9: if candidate is corrupted and it is the last candidate, self.torrent_corrupted sets to true
        ## TC 10: if candidate is corrupted and it is the last candidate, self.torrent_corrupted sets to false
        #self.actual_pos should contain the value of self.last_file_marker
        ## TC 11: always compute seek while processing candidates
        ## TC 12: storing last valid file piece in case of we're at the end of the file

        # TC 13 def test_does_not_process_files_should_skip(self):


        ###GENERATOR, find_candidates_for_all_files:
        ## TC 14: skips the unwanted extensions
        ## TC 15: test whether candidates put under the correct key
        ## TC 16: single torrent case, candidates are searched

    def setUp(self):
        self.PathAndLength = namedtuple('PathAndLength', 'path length')

        self.temp_dir = TempDirectory()
        self.temp_dir_path = self.temp_dir.path
        self.temp_dir.write('a/b1/a.b1.f1', ContentManager.generate_random_binary(123454).getvalue())
        self.temp_dir.write('a/b1/a.b1.f2', ContentManager.generate_random_binary(123454).getvalue())
        self.temp_dir.write('b/b2/b.b2.f1', ContentManager.generate_random_binary(123455).getvalue())
        self.file_finder = FileFinder()
        self.file_finder.cache_files_by_size([self.temp_dir.path])

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_candidates_for_all_files(self):
        paths = [self.PathAndLength('path1', 123454), self.PathAndLength('path2', 123455)]
        mock_torrent = MockTorrentFile('name', paths, 2500)
        generator = Generator(mock_torrent.meta_info, self.file_finder, DUMMY_MEDIA_DIR, DUMMY_DEST_DIR)

        self.assertEqual(2, len(generator.candidates.keys()))
        self.assertListEqual([os.path.join(self.temp_dir_path, 'a', 'b1', 'a.b1.f1'),
                              os.path.join(self.temp_dir_path, 'a', 'b1', 'a.b1.f2')],
                             generator.candidates['path1'])
        self.assertListEqual([os.path.join(self.temp_dir_path, 'b', 'b2', 'b.b2.f1')], generator.candidates['path2'])

    @tempdir()
    def test_find_candidates_for_all_files_skips_unwanted_exts(self, temp_dir):
        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('path1', 123454),
                 self.PathAndLength('path2', 123455),
                 self.PathAndLength('path.txt', 12),
                 self.PathAndLength('path.nfo', 12)]
        mock_torrent = MockTorrentFile('name', paths, 2500)

        generator = Generator(mock_torrent.meta_info, self.file_finder, DUMMY_MEDIA_DIR, DUMMY_DEST_DIR)

        self.assertEqual(2, len(generator.candidates.keys()))
        self.assertListEqual([os.path.join(self.temp_dir_path, 'a', 'b1', 'a.b1.f1'),
                              os.path.join(self.temp_dir_path, 'a', 'b1', 'a.b1.f2')],
                             generator.candidates['path1'])
        self.assertListEqual([os.path.join(self.temp_dir_path, 'b', 'b2', 'b.b2.f1')], generator.candidates['path2'])


    def test_last_skipped_number_of_pieces_set_if_no_candidates_are_found(self):
        lengths = [123454, 123789]
        paths = [self.PathAndLength('path1', lengths[0]), self.PathAndLength('path2', lengths[1])]
        mock_torrent = MockTorrentFile('name', paths, PIECE_LENGTH)

        generator = Generator(mock_torrent.meta_info, self.file_finder, DUMMY_MEDIA_DIR, DUMMY_DEST_DIR)
        numbered = enumerate(generator.pieces_generator())
        for i, piece in numbered:
            pass

        self.assertEqual(sum(lengths), generator.actual_pos)
        self.assertEqual(123789, generator.last_file_marker)

    @tempdir()
    def test_generate_random_data(self, temp_dir):
        lengths = [123454, 123789]

        temp_dir.write('b/b1/b.b1.f1', ContentManager.generate_random_binary(1).getvalue())
        temp_dir.write('c/c1/c.c1.f1.nfo', ContentManager.generate_random_binary(12).getvalue())
        temp_dir.write('c/c1/c.c1.f2.txt', ContentManager.generate_random_binary(12).getvalue())

        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('path1', lengths[0]), self.PathAndLength('path2', lengths[1])]
        mock_torrent = MockTorrentFile('name', paths, PIECE_LENGTH)

        generator = Generator(mock_torrent.meta_info, self.file_finder, DUMMY_MEDIA_DIR,
                              DUMMY_DEST_DIR)

        numbered = enumerate(generator.pieces_generator())
        for i, piece in numbered:
            pass

        # 123454 has one candidate, 123789 has 0 -->last_file_marker should be the 123789
        self.assertEqual(sum(lengths), generator.actual_pos)
        self.assertEqual(123789, generator.last_file_marker)

    @tempdir()
    def test_generator_skips_two_not_wanted_files_and_reads_appropriate_data_from_wanted_file(self, temp_dir):
        filepaths = ['c/c1/c.c1.f1.nfo', 'c/c1/c.c1.f2.txt', 'c/c1/c.c1.f3.mp3']

        piece_length = 32
        length_of_valid_file = 567
        temp_dir.write(filepaths[0], ContentManager.generate_seq_data(10).getvalue())
        temp_dir.write(filepaths[1], ContentManager.generate_seq_data(20).getvalue())
        temp_dir.write(filepaths[2], ContentManager.generate_seq_data(567).getvalue())


        self.file_finder.cache_files_by_size([temp_dir.path])

        paths = [self.PathAndLength('f1.nfo', 10),
                 self.PathAndLength('f2.txt', 20),
                 self.PathAndLength('f3.mp3', length_of_valid_file)]

        filepaths = [os.path.abspath(os.path.join(temp_dir.path, fp)) for fp in filepaths]

        mock_torrent = MockTorrentFile('name', paths, piece_length, real_filepaths=filepaths)

        generator = Generator(mock_torrent.meta_info, self.file_finder, DUMMY_MEDIA_DIR,
                              DUMMY_DEST_DIR)

        filepath = os.path.join(temp_dir.path, filepaths[2])

        offset = 10 + 20
        skipped_pieces = 1 + (offset / piece_length)
        file_seek = (skipped_pieces * piece_length) - offset

        positions = ContentManager.get_file_positions(length_of_valid_file, piece_length, initial_seek=file_seek)

        file_pieces = [ContentManager.get_bytes_from_file(filepath, p[0], p[1]) for p in positions]

        numbered = enumerate(generator.pieces_generator())
        actual_pieces = [piece for i, piece in numbered]
        self.assertEqual(len(file_pieces), len(actual_pieces))
        self.assertListEqual(file_pieces, actual_pieces)



