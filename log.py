import os
import sys
import time
import logging


def calcLogName():
    defpath = '/var/log/photo-importer'

    fname = time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime()) + '.log'

    return os.path.join(defpath, fname)


def initLogger(filename=None):
    if filename is not None:
        try:
            os.makedirs(os.path.split(filename)[0])
        except OSError:
            pass
        #init file logger and console
        fh = logging.FileHandler(filename, 'a')
    else:
        #init only console
        fh = logging.StreamHandler()

    form = '[%(asctime)s] [%(levelname)s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    fmt = logging.Formatter(form, datefmt)
    fh.setFormatter(fmt)
    logging.getLogger().addHandler(fh)

    logging.getLogger().setLevel(logging.INFO)

    logging.info('Log file: ' + str(filename))
    logging.debug(str(sys.argv))
