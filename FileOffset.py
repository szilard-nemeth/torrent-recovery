__author__ = 'szyszy'

import os


class FileOffset:
    @staticmethod
    def determine_offsets(metainfo, candidates, exts_to_skip):
        ongoing = False
        running_sum = 0
        tmp_start = 0
        tmp_end = 0
        offsets = []
        if 'files' in metainfo:
            for file_info in metainfo['files']:
                length = file_info['length']
                path = file_info['path'][0]
                extension = os.path.splitext(path)[1]
                if extension[:1] == '.': extension = extension[1:]

                if extension in exts_to_skip or len(candidates[path]) == 0:
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

            # #could miss if the last files were unwanted! (does not go into else)
            if tmp_end > 0:
                offsets.append((tmp_start, tmp_end))

        return offsets