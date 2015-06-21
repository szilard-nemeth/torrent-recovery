import sys
import os
import hashlib
import StringIO
import bencode
import pprint
import argparse
import logging
import DefaultTorrentDataProvider
from FileFinder import FileFinder
from Generator import Generator


class TorrentRecovery:
    def __init__(self, media_dirs, dest_dir, torrent_data_provider):
        self.log = logging.getLogger('torrent_recovery')
        self.media_dirs = media_dirs
        self.dest_dir = dest_dir
        self.torrent_data_provider = torrent_data_provider
        self.fileFinder = FileFinder()

    def start(self):
        self.log.info('Starting to cache files by size....')
        self.fileFinder.cache_files_by_size(self.media_dirs)

        for idx, info in enumerate(self.torrent_data_provider.generator()):
            self.log.info('processing %d out of %d, file: %s', idx + 1, self.torrent_data_provider.get_file_count(), file)
            self.log.info('===============================================')
            self.process_torrent(info)
            self.log.info('===============================================')

    def process_torrent(self, info):
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('metainfo: %s', pprint.pformat(info))

        self.generator = Generator(info, self.fileFinder, self.media_dirs, self.dest_dir)
        pieces = StringIO.StringIO(info['pieces'])

        # Iterate through pieces
        last_file_pos = 0
        for piece in self.generator.pieces_generator():
            if self.generator.torrent_corrupted:
                self.log.warning('torrent corrupted: %s', info['name'])
                break
            # Compare piece hash with expected hash
            piece_hash = hashlib.sha1(piece).digest()
            # seek the offset (skip unwanted files)
            if self.generator.new_candidate:
                #save the actual position of pieces corresponding to the
                #0th byte of any relevant file
                last_file_pos = pieces.tell()
            pieces.seek(self.generator.get_last_number_of_skipped_pieces() * 20, os.SEEK_CUR)

            if piece_hash != pieces.read(20):
                self.generator.corruption()
                pieces.seek(last_file_pos)
        # ensure we've read all pieces
        if pieces.read():
            self.generator.corruption()

    @staticmethod
    def setup_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose', default=None, required=False,
                            help='more verbose log')
        parser.add_argument('--media_dirs', type=check_file, required=True, nargs='+',
                            help='list of dirs where media is')
        parser.add_argument('--torrent_files_dir', type=check_file, required=True,
                            help='a dir where torrentfiles are')
        parser.add_argument('--destination_dir', type=check_file, required=True,
                            help='a dir where the moved data will reside')
        return parser

    @staticmethod
    def create_args_dict(arg_parser):
        args = arg_parser.parse_args()
        log = logging.getLogger('torrent_recovery')
        log.debug(args)

        argsDict = vars(args)
        # #deletes null keys
        argsDict = dict((k, v) for k, v in argsDict.items() if v)
        if log.isEnabledFor(logging.DEBUG):
            log.info("args dict: %s", pprint.pformat(argsDict))
        return argsDict

    @staticmethod
    def init_logger(verbose):
        # TODO use dictConfig instead
        #https://docs.python.org/2/library/logging.config.html#logging-config-api
        #FORMAT = '%(asctime)-15s   %(message)s'
        #logging.basicConfig(format=FORMAT, level=logging.DEBUG)
        logger = logging.getLogger('torrent_recovery')
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('torrent_recovery.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        if verbose:
            ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger


def check_file(file):
    if not os.path.exists(file):
        raise argparse.ArgumentError("{0} does not exist".format(file))
    return file


def main():
    arg_parser = TorrentRecovery.setup_parser()
    argsDict = TorrentRecovery.create_args_dict(arg_parser)
    verbose = True if 'verbose' in argsDict else False
    logger = TorrentRecovery.init_logger(verbose)

    media_dirs = argsDict['media_dirs']
    torrentfiles_dir = argsDict['torrent_files_dir']
    destination_dir = argsDict['destination_dir']

    torrentfiles_list = FileFinder.find_torrent_files(torrentfiles_dir)
    logger.info('Found %d torrent files in %s', len(torrentfiles_list), torrentfiles_dir)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('torrentfiles: %s', pprint.pformat(torrentfiles_list))

    torrent_provider = DefaultTorrentDataProvider(torrentfiles_list)

    recovery = TorrentRecovery(media_dirs, destination_dir, torrent_provider)
    recovery.start()


if __name__ == "__main__":
    main()