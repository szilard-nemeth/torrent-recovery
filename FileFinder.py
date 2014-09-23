__author__ = 'szyszy'

import os
import logging
from timed_wrapper import timed

class FileFinder:

    def __init__(self):
        self.log = logging.getLogger('torrent_recovery.FileFinder')


    @staticmethod
    def find_candidate_files_matching_size(length, dir):
        list_of_files = []
        for root, dirs, files in os.walk(dir):
            for name in files:
                file_length = os.stat(os.path.join(root, name)).st_size
                if length == file_length:
                    list_of_files.append(os.path.join(root, name))
        return list_of_files

    @timed
    def cache_files_by_size(self, param_dirs):
        self.files_by_size = {}
        for dir in param_dirs:
            self.log.info('caching: %s', dir)
            for root, dirs, files in os.walk(dir):
                for name in files:
                    filename = os.path.join(root, name)
                    file_length = os.stat(filename).st_size
                    if file_length in self.files_by_size:
                        self.files_by_size[file_length].append(filename)
                    else:
                        self.files_by_size[file_length] = [filename]

    def find_candidate_files_matching_size_from_cache(self, length):
        if length in self.files_by_size:
            return self.files_by_size[length]
            #return sorted(self.files_by_size[length])
        else:
            return []

    @staticmethod
    def find_torrent_files(dir):
        list_of_files = []
        for root, dirs, files in os.walk(dir):
            for name in files:
                if name.endswith(".torrent"):
                    list_of_files.append(os.path.join(root, name))
        return list_of_files