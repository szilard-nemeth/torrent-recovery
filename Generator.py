__author__ = 'szyszy'

import os
import StringIO
import logging
from FileFinder import FileFinder

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


class Generator:
    def __init__(self, metainfo, fileFinder, media_dirs, dest_dir):
        self.log = logging.getLogger('torrent_recovery.generator')
        self.fileFinder = fileFinder
        self.metainfo = metainfo
        self.media_dirs = media_dirs
        self.dest_dir = dest_dir

        self.pieces = StringIO.StringIO(metainfo['pieces'])
        self.piece_length = metainfo['piece length']
        self.candidate_corrupted = False
        self.torrent_corrupted = False

        self.exts_to_skip = ['sfv', 'nfo', 'm3u', 'jpg', 'jpeg', 'txt']

        self.candidates = self.find_candidates_for_all_files()
        self.offsets = self.determine_offsets()
        self.last_skipped_number_of_pieces = 0
        self.actual_pos = 0
        self.last_file_marker = 0
        self.new_candidate = False



    def determine_offsets(self):
        ongoing = False
        running_sum = 0
        tmp_start = 0
        tmp_end = 0
        offsets = []
        if 'files' in self.metainfo:
            for file_info in self.metainfo['files']:
                length = file_info['length']

                extension = os.path.splitext(file_info['path'][0])[1]
                if extension[:1] == '.': extension = extension[1:]

                if extension in self.exts_to_skip or len(self.candidates[file_info['path'][0]]) == 0:
                    if not ongoing:
                        ongoing = True
                        tmp_start = running_sum
                        tmp_end = tmp_start + length
                    else:
                        tmp_end += length
                else:
                    if ongoing:
                        ongoing = False
                        offsets.append((tmp_start, tmp_end))
                        tmp_start = 0
                        tmp_end = 0
                running_sum += length

            ##could miss if the last files were unwanted! (does not go into else)
            if tmp_end > 0:
                offsets.append((tmp_start, tmp_end))

        return offsets


    def find_candidates_for_all_files(self):
        candidates_map = {}
        if 'files' in self.metainfo:
            piece = ""
            for file_info in self.metainfo['files']:

                extension = os.path.splitext(file_info['path'][0])[1]
                if extension[:1] == '.': extension = extension[1:]
                if extension in self.exts_to_skip:
                    continue

                length = file_info['length']
                candidates = self.fileFinder.find_candidate_files_matching_size_from_cache(length)
                candidates_map[file_info['path'][0]] = candidates


                if len(candidates_map[file_info['path'][0]]) == 0:
                    self.log.warning('NO candidates for %s!', file_info['path'][0])
                elif len(candidates_map[file_info['path'][0]]) > 1:
                    self.log.warning('multiple candidates for %s!', file_info['path'][0])
                    self.log.warning(candidates_map[file_info['path'][0]])


        else:
            length = self.metainfo['length']
            candidates = self.fileFinder.find_candidate_files_matching_size_from_cache(length)
            candidates_map[self.metainfo['name']] = candidates
        return candidates_map


    def pieces_generator(self):
        """Yield pieces from download file(s)."""
        if 'files' in self.metainfo:  # yield pieces from a multi-file torrent
            piece = ""
            last_valid_file_piece = (0, "")
            #TODO filter it before processing!
            for file_idx, file_info in enumerate(self.metainfo['files']):
                extension = os.path.splitext(file_info['path'][0])[1]
                if extension[:1] == '.': extension = extension[1:]
                if extension in self.exts_to_skip:
                    continue

                candidates = self.candidates[file_info['path'][0]]
                if len(candidates) == 0:
                    length = file_info['length']
                    #sets last number of skipped pieces
                    self.compute_seek(self.actual_pos, length)
                    self.actual_pos += length
                    self.last_file_marker += length


                for idx, candidate in enumerate(candidates):
                    #TODO  use with open('workfile', 'r') as f:
                    #https://docs.python.org/2/tutorial/inputoutput.html#methods-of-file-objects
                    sfile = open(candidate.decode('UTF-8'), "rb")
                    self.last_file_marker = self.actual_pos
                    self.new_candidate = True

                    #just take care of the last valid piece if this is a neighbor file
                    if last_valid_file_piece[0] == (file_idx - 1):
                        piece = last_valid_file_piece[1]
                    #if idx > 0:
                    #    piece = ""
                    while True:
                        if self.candidate_corrupted:
                            bytes_read_from_current_candidate = self.actual_pos - self.last_file_marker
                            self.log.warning('candidate %s is corrupt', candidate)
                            percentage = float(bytes_read_from_current_candidate) / float(file_info['length']) * 100
                            self.log.warning('candidate %s (for %s): bytes read: %d / %d ( %d %% )', candidate,
                                             file_info['path'][0],
                                             bytes_read_from_current_candidate, file_info['length'], percentage)

                            if idx == (len(candidates) - 1):
                                self.torrent_corrupted = True
                                break
                            else:
                                self.candidate_corrupted = False
                                #fall back to next candidate
                                self.actual_pos = self.last_file_marker
                                break

                        would_read = self.piece_length - len(piece)
                        computed_seek = self.compute_seek(self.actual_pos, would_read)
                        if computed_seek > 0:
                            sfile.seek(computed_seek)
                        piece += sfile.read(would_read)

                        tmp_actual_pos = self.actual_pos
                        if self.new_candidate:
                            #increase just with would_read if new file is being processed
                            # (may be less than piece (piece in this case is piece_length)

                            self.actual_pos += would_read
                        else:
                            self.actual_pos += len(piece)
                        self.log.debug('increased actual pos: %d --> %d (+ %d) ', tmp_actual_pos, self.actual_pos, self.actual_pos - tmp_actual_pos)

                        #this marks the end of file is reached
                        if len(piece) != self.piece_length:
                            sfile.close()
                            last_valid_file_piece = (file_idx, piece)
                            break

                        yield piece
                        self.new_candidate = False
                        #do not delete the remainder piece when candidate was corrupt (next file may need this piece)
                        #delete only when candidate is still not corrupt OR torrent is corrupt (next torrent don't want this piece)
                        #if (not self.candidate_corrupted):# or self.torrent_corrupted:
                        piece = ""

                    if sfile.closed:
                        dest = os.sep.join([self.dest_dir] + [self.metainfo['name']] + file_info['path'])
                        self.log.info('MOVE: %s -->  %s', candidate, dest)
                        #do not check other candidates
                        break

                self.log.debug('actual pos is %d after read file %s: ', self.actual_pos, file_info['path'][0])
            if piece != "":
                yield piece
                self.new_candidate = False
        else:  # yield pieces from a single file torrent
            candidates = self.candidates[self.metainfo['name']]
            for candidate in candidates:
                sfile = open(candidate.decode('UTF-8'), "rb")
                while True:
                    piece = sfile.read(self.piece_length)
                    if not piece:
                        sfile.close()
                        return
                    yield piece

    def corruption(self):
        self.candidate_corrupted = True

    def get_number_of_skipped_pieces(self, offset):
        base = 0
        if offset > 0:
            base += 1

        return (offset / self.piece_length) + base

    def compute_seek(self, actual_pos, would_read):
        for (start, end) in self.offsets:
            if actual_pos >= start and (not actual_pos > end):
                offset = end - start
                num = self.get_number_of_skipped_pieces(offset)
                self.last_skipped_number_of_pieces += num
                return (num * self.piece_length) - offset

        self.last_skipped_number_of_pieces = 0
        return 0

    def get_last_number_of_skipped_pieces(self):
        tmp = self.last_skipped_number_of_pieces
        self.last_skipped_number_of_pieces = 0
        return tmp

