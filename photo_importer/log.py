import io
import os
import sys
import time
import logging

LOGFMT = '[%(asctime)s] [%(levelname)s] %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'


def calcLogName():
    defpath = '/var/log/photo-importer'

    fname = time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime()) + '.log'

    return os.path.join(defpath, fname)


def initLogger(filename=None, level=logging.INFO):
    if filename is not None:
        try:
            os.makedirs(os.path.split(filename)[0])
        except OSError:
            pass
        fh = logging.FileHandler(filename, 'a')
    else:
        fh = logging.StreamHandler()

    fmt = logging.Formatter(LOGFMT, DATEFMT)
    fh.setFormatter(fmt)
    logging.getLogger().addHandler(fh)

    logging.getLogger().setLevel(level)

    logging.info('Log file: ' + str(filename))
    logging.debug(str(sys.argv))


class MemLogger(object):
    def __init__(self, name):
        self.__name = name
        fmt = logging.Formatter(LOGFMT, DATEFMT)
        self.__stream = io.StringIO()
        self.__handler = logging.StreamHandler(self.__stream)
        self.__handler.setFormatter(fmt)
        logging.getLogger().addHandler(self.__handler)
        logging.info("MemLogger " + self.__name + " started")

    def __del__(self):
        logging.getLogger().removeHandler(self.__handler)
        logging.info("MemLogger " + self.__name + " finished")

    def get_text(self):
        return self.__stream.getvalue()
