import os

__author__ = 'szyszy'

from StringIO import StringIO


class ContentManager:

    @staticmethod
    def generate_random_binary(length):
        return StringIO(os.urandom(length))
