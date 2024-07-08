import io
import os
import sys
import logging

LOGFMT = '[%(asctime)s] [%(levelname)s] %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'


def init_logger(filename=None, level=logging.INFO):
    if filename is not None:
        try:
            os.makedirs(os.path.split(filename)[0])
        except OSError:
            pass
        mode = 'a' if os.path.isfile(filename) else 'w'
        fh = logging.FileHandler(filename, mode)
    else:
        fh = logging.StreamHandler()

    fmt = logging.Formatter(LOGFMT, DATEFMT)
    fh.setFormatter(fmt)
    logging.getLogger().addHandler(fh)

    logging.getLogger().setLevel(level)

    logging.info('Log file: %s', filename)
    logging.debug(str(sys.argv))


class MemLogger:
    def __init__(self, name):
        self.__name = name
        fmt = logging.Formatter(LOGFMT, DATEFMT)
        self.__stream = io.StringIO()
        self.__handler = logging.StreamHandler(self.__stream)
        self.__handler.setFormatter(fmt)
        logging.getLogger().addHandler(self.__handler)
        logging.info("MemLogger %s started", self.__name)

    def __del__(self):
        logging.getLogger().removeHandler(self.__handler)
        logging.info("MemLogger %s finished", self.__name)

    def get_text(self):
        return self.__stream.getvalue()
