__author__ = 'szyszy'

from functools import wraps
from time import time
import logging

def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        log = logging.getLogger('torrent_recovery')
        start = time()
        result = f(*args, **kwds)
        elapsed = time() - start
        log.info("%s took %d seconds to finish", f.__name__, elapsed)
        return result
    return wrapper