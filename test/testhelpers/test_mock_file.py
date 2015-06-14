import os

__author__ = 'szyszy'

from StringIO import StringIO


class ContentManager:
    def __init__(self, mock_fs_helper, torrent_to_mockfile_mappings):
        self.mock_fs_helper = mock_fs_helper
        self.binary_contents = {}
        self.generate_binary_contents_for_files(torrent_to_mockfile_mappings)

    def generate_binary_contents_for_files(self, torrent_to_mockfile_mappings):
        # #TODO make this better
        sizes_dict = self.mock_fs_helper.get_last_sizes_dict()
        for torrent_path, mockfiles in torrent_to_mockfile_mappings.iteritems():
            #mockfile_paths = [mockfile.path for mockfile in mockfiles]
            for mockfile in mockfiles:
                for size, real_paths in sizes_dict.iteritems():
                    if mockfile.path in real_paths:
                        mockfile.data = self.generate_random_binary(size)
                        #MockFileStore.register(mockfile)

    @staticmethod
    def generate_random_binary(length):
        return StringIO(os.urandom(length))
