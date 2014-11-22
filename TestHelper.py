from unittest.test.test_result import __init__

__author__ = 'szyszy'

from test_mock_file_fs import MockFs
from test_mock_file_fs import MockOs
from mock import MagicMock
from FileFinder import FileFinder

class MockFsHelper:

    def __init__(self, mock_os, add_defaults=False):
        self.filefinder = FileFinder()
        self.fs = MockFs(add_defaults)
        MockOs.init(self.fs, mock_os)

    def add_dir(self, dir):
        return self.fs.add_dir(dir)

    def add_files(self, files):
        return self.fs.add_files(files)

    def cache_in_filefinder(self):
        dirs = MagicMock()
        dirs.__iter__.return_value = self.fs.get_top_level_dirs()
        self.filefinder.cache_files_by_size(dirs)

    def get_last_sizes_dict(self):
        return self.fs.get_last_sizes_dict()