import hashlib
import os
import string

__author__ = 'szyszy'

from StringIO import StringIO

#TODO test there methods!
class ContentManager:
    @staticmethod
    def generate_random_binary(length):
        return StringIO(os.urandom(length))

    @staticmethod
    def generate_seq_data(length):
        alphabet = list(string.ascii_lowercase)

        output = []
        alphabet_length = len(alphabet)
        for i in range(0, length):
            output.append(alphabet[i % alphabet_length])
        output = ''.join(str(item) for item in output)
        return StringIO(output)

    @staticmethod
    def generate_hash_from_files(filepaths):
        string_buffer = StringIO()
        for path in filepaths:
            f = open(path, 'rb')
            try:
                string_buffer.write(f.read())
            finally:
                f.close()

        all_contents = string_buffer.getvalue()
        string_buffer.close()
        return hashlib.sha1(all_contents).digest()


    @staticmethod
    def get_bytes_from_file(filepath, from_pos, to_pos):
        f = open(filepath, 'rb')
        f.seek(from_pos)

        length_to_read = to_pos - from_pos
        return f.read(length_to_read)

    @staticmethod
    def get_file_positions(length_of_file, piece_length, initial_seek=0):
        positions = []

        from_pos = 0
        to_pos = 0
        if initial_seek > 0:
            from_pos = initial_seek
            to_pos = initial_seek + piece_length
            positions.append((from_pos, to_pos))

        while to_pos < length_of_file:
            from_pos = to_pos
            to_pos = from_pos + piece_length

            if from_pos > length_of_file:
                from_pos = length_of_file
            if to_pos > length_of_file:
                to_pos = length_of_file
            positions.append((from_pos, to_pos))

        return positions