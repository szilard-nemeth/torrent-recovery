__author__ = 'szyszy'

# ##SINGLE FILE TORRENT EXAMPLE
# info:
# {'file-duration': [306],
# 'file-media': [0],
# 'length': 350282805,
# 'name': 'Xyz.wmv',
# 'piece length': 524288,
#  'pieces': '\xe0\x99\xa6\x81\x1d6\xbbey]\x83p\xcd\x1c<v2\x83\xe5\x19\xb0\t/U\xff......
#  'private': 1,
#  'profiles': [{'acodec': '', 'height': 1080, 'vcodec': '', 'width': 1920}],
#  'source': 'xyz.com'}

###MULTI FILE TORRENT EXAMPLE
# info:
# {'files': [{'length': 80,
#             'path': ['00-mark_sixma-requiem-web-2013-ukhx.m3u']},
#            {'length': 5654,
#             'path': ['00-mark_sixma-requiem-web-2013-ukhx.nfo']},
#            {'length': 100,
#             'path': ['00-mark_sixma-requiem-web-2013-ukhx.sfv']},
#            {'length': 13484451,
#             'path': ['01-mark_sixma-requiem_(original_mix).mp3']},
#            {'length': 8905708,
#             'path': ['02-mark_sixma-requiem_(radio_edit).mp3']}],
#  'name': 'Mark_Sixma-Requiem-WEB-2013-UKHx',
#  'piece length': 1048576,
#  'pieces': '\xae\xfa\x1a4t\x83\xf8=S"E"\xefa\x19\xb8#\x94\xf8p\x8e(bW@@>\xbb\xc1<\.......
#  'private': 1}
class MockTorrentFile:
    def __init__(self, name, filenames_and_lengths, piece_length):
        self.meta_info = self.create_meta_info(name, filenames_and_lengths, piece_length)

    def create_meta_info(self, name, filenames_and_lengths, piece_length):
        result = dict()
        result['name'] = name
        result['piece length'] = piece_length
        result['pieces'] = self.generate_pieces()

        if len(filenames_and_lengths) == 1:
            result['length'] = filenames_and_lengths[0].length
        else:
            result['files'] = []
            for filename_and_length in filenames_and_lengths:
                d = dict()
                d['length'] = filename_and_length.length
                d['path'] = [filename_and_length.path]
                result['files'].append(d)
        return result

    def generate_pieces(self):
        return None