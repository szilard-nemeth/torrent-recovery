__author__ = 'szyszy'

class TestTorrentDataProvider:
    def __init__(self, mock_torrents):
        self.mock_torrents = mock_torrents

    def generator(self):
        for mock_torrent in self.mock_torrents:
            yield mock_torrent.meta_info

    def get_file_count(self):
        return len(self.mock_torrents)