#!/usr/bin/python3

import logging
import argparse
import threading
import progressbar

from . import log
from . import config
from . import importer


class ProgressBar(threading.Thread):
    def __init__(self, imp):
        threading.Thread.__init__(self)
        self.__imp = imp
        self.__pbar = None

    def __create(self, name, count):
        if count == 0:
            return

        if self.__pbar:
            self.__pbar.finish()
            self.__pbar = None

        self.__pbar = progressbar.ProgressBar(
            maxval=count,
            widgets=[
                name,
                ' ',
                progressbar.Percentage(),
                ' ',
                progressbar.Bar(),
                ' ',
                progressbar.ETA(),
            ],
        ).start()

    def run(self):
        stage = ''
        while True:
            stat = self.__imp.status()

            if stage != stat['stage']:
                stage = stat['stage']
                if stage == 'scan':
                    print('Scan... ', end='', flush=True)
                    continue
                if stage == 'move':
                    print('Done. Found %i files' % stat['total'])
                    self.__create('Import:', stat['total'])
                    continue
                if stage == 'rotate':
                    self.__create('Rotate:', stat['total'])
                    continue
                if stage == 'done':
                    if self.__pbar:
                        self.__pbar.finish()
                    break

            if (
                stage == 'move' or stage == 'rotate'
            ) and self.__pbar is not None:
                self.__pbar.update(stat[stage]['processed'])


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_path', help='Input path')
    parser.add_argument('out_path', help='Output path', nargs='?')
    parser.add_argument('-c', '--config', help='Config file')
    parser.add_argument('-l', '--logfile', help='Log file', default='log.txt')
    parser.add_argument('-d', '--dryrun', help='Dry run', action='store_true')
    return parser.parse_args()


def main():
    args = args_parse()

    cfg = config.Config(args.config)

    log.initLogger(args.logfile)

    imp = importer.Importer(cfg, args.in_path, args.out_path, args.dryrun)

    pbar = ProgressBar(imp)
    imp.start()
    pbar.start()
    imp.join()
    pbar.join()

    status = imp.status()
    logging.info('status: %s' % str(status))
    if status['move']['errors'] != 0 or status['rotate']['errors'] != 0:
        print('Some errors found. Please check log file.')


if __name__ == '__main__':
    main()
