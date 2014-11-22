__author__ = 'szyszy'

import os
import logging
from timed_wrapper import timed


class FileFinder:
    def __init__(self):
        self.files_by_size = {}
        self.log = logging.getLogger('torrent_recovery.FileFinder')

    # @timed
    def cache_files_by_size(self, param_dirs):
        for dir in param_dirs:
            self.log.info('caching: %s', dir)
            for root, dirs, files in os.walk(dir):
                for name in files:
                    filename = os.path.abspath(os.path.join(root, name))
                    file_length = os.stat(filename).st_size
                    if file_length in self.files_by_size:
                        self.files_by_size[file_length].append(filename)
                    else:
                        self.files_by_size[file_length] = [filename]

    def find_candidate_files_matching_size_from_cache(self, length):
        if length in self.files_by_size:
            return self.files_by_size[length]
            # TODO check that what changes if sort is on
            # return sorted(self.files_by_size[length])
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


    def find_candidates_for_all_files(self, metainfo, exts_to_skip):
        candidates_map = {}
        if 'files' in metainfo:
            piece = ""
            for file_info in metainfo['files']:
                extension = os.path.splitext(file_info['path'][0])[1]
                if extension[:1] == '.': extension = extension[1:]
                if extension in exts_to_skip:
                    continue

                length = file_info['length']
                candidates = self.find_candidate_files_matching_size_from_cache(length)
                candidates_map[file_info['path'][0]] = candidates

                if len(candidates_map[file_info['path'][0]]) == 0:
                    self.log.warning('NO candidates for %s!', file_info['path'][0])
                elif len(candidates_map[file_info['path'][0]]) > 1:
                    self.log.warning('multiple candidates for %s!', file_info['path'][0])
                    self.log.warning(candidates_map[file_info['path'][0]])

        else:
            length = metainfo['length']
            candidates = self.find_candidate_files_matching_size_from_cache(length)
            candidates_map[metainfo['name']] = candidates
        return candidates_map