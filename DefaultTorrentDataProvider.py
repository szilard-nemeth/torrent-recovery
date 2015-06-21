import bencode

__author__ = 'szyszy'

class DefaultTorrentDataProvider:
    def __init__(self, file_list):
        self.file_list = file_list

    def generator(self):
        for torrent_file in self.file_list:
            torrent_file = open(torrent_file, "rb")
            metainfo = bencode.bdecode(torrent_file.read())
            info = metainfo['info']
            yield info

    def get_file_count(self):
        return len(self.file_list)