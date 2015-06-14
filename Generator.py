__author__ = 'szyszy'

import os
import StringIO
import logging
from FileFinder import FileFinder
from FileOffset import FileOffset


class Generator:
    def __init__(self, metainfo, filefinder, media_dirs, dest_dir):
        self.log = logging.getLogger('torrent_recovery.generator')
        self.fileFinder = filefinder
        self.metainfo = metainfo
        self.media_dirs = media_dirs
        self.dest_dir = dest_dir

        self.pieces = StringIO.StringIO(metainfo['pieces'])
        self.piece_length = metainfo['piece length']
        self.candidate_corrupted = False
        self.torrent_corrupted = False

        self.exts_to_skip = ['sfv', 'nfo', 'm3u', 'jpg', 'jpeg', 'txt']

        self.candidates = self.fileFinder.find_candidates_for_all_files(self.metainfo, self.exts_to_skip)
        self.offsets = FileOffset.determine_offsets(self.metainfo, self.candidates, self.exts_to_skip)
        self.last_skipped_number_of_pieces = 0
        self.actual_pos = 0
        self.last_file_marker = 0
        self.new_candidate = False



    def pieces_generator(self):
        """Yield pieces from downloaded file(s)."""
        if 'files' in self.metainfo:  # yield pieces from a multi-file torrent
            piece = ""
            last_valid_file_piece = (0, "")
            # TODO filter it before processing!
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
                        self.log.debug('increased actual pos: %d --> %d (+ %d) ', tmp_actual_pos, self.actual_pos,
                                       self.actual_pos - tmp_actual_pos)

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

