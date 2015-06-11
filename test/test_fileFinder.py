import unittest
import os

from testfixtures import tempdir

from FileFinder import FileFinder


__author__ = 'szyszy'


class TestFileFinder(unittest.TestCase):

    def setUp(self):
        self.file_finder = FileFinder()

    #TODO add more testcases to FileFinder
    #TODO start to use generate_random_binary for file contents
    @tempdir()
    def test_cache_files_by_size(self, temp_dir):
        temp_dir.write('a/b/c', b'1234')
        temp_dir.write('a/b/d', b'12345')
        temp_dir.write('a/b/e', b'123456')

        self.file_finder.cache_files_by_size([temp_dir.path])

        expected_dict = {
            4: [os.path.join(temp_dir.path, 'a', 'b', 'c')],
            5: [os.path.join(temp_dir.path, 'a', 'b', 'd')],
            6: [os.path.join(temp_dir.path, 'a', 'b', 'e')],
        }
        self.assertDictEqual(expected_dict, self.file_finder.files_by_size)

    @tempdir()
    def test_cache_files_by_size_differentiates_two_same_named_subfolders(self, temp_dir):
        temp_dir.write('a/b1/f1', b'12345')
        temp_dir.write('b/b1/f1', b'123456789')

        self.file_finder.cache_files_by_size([temp_dir.path])

        expected_dict = {
            5: [os.path.join(temp_dir.path, 'a', 'b1', 'f1')],
            9: [os.path.join(temp_dir.path, 'b', 'b1', 'f1')],
        }
        self.assertDictEqual(expected_dict, self.file_finder.files_by_size)

    @tempdir()
    def test_find_candidate_files_from_cache(self, temp_dir):
        temp_dir.write('a/a1/a.a1.f1', b'1234')
        temp_dir.write('b/b1/b.b1.f1', b'1234567')
        temp_dir.write('c/c1/c.c1.f1', b'123456789')
        temp_dir.write('c/c1/c.c1.f2', b'123456789')

        self.file_finder.cache_files_by_size([temp_dir.path])

        self.assertListEqual([os.path.join(temp_dir.path, 'a', 'a1', 'a.a1.f1')],
                             self.file_finder.find_candidate_files_matching_size_from_cache(4))
        self.assertListEqual([os.path.join(temp_dir.path, 'b', 'b1', 'b.b1.f1')],
                             self.file_finder.find_candidate_files_matching_size_from_cache(7))
        self.assertListEqual([os.path.join(temp_dir.path, 'c', 'c1', 'c.c1.f1'),
                              os.path.join(temp_dir.path, 'c', 'c1', 'c.c1.f2')],
                             self.file_finder.find_candidate_files_matching_size_from_cache(9))
