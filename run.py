#!/usr/bin/python3

import sys
import log
import time
import argparse
import threading
import progressbar

import config
import importer


class ProgressBar(threading.Thread):
    def __init__(self, imp):
        threading.Thread.__init__(self)
        self.__imp = imp
        self.__pbar = None

    def __create(self, name, count):
        if self.__pbar:
            self.__pbar.finish()
            self.__pbar = None

        self.__pbar = progressbar.ProgressBar(
            maxval=count,
            widgets=[
                name, ' ',
                progressbar.Percentage(), ' ',
                progressbar.Bar(), ' ',
                progressbar.ETA()]).start()

    def run(self):
        stage = ''
        while True:
            time.sleep(0.1)
            stat = self.__imp.status()

            if stage != stat['stage']:
                stage = stat['stage']
                if stage == 'scan':
                    print('Scan...')
                    continue
                if stage == 'move':
                    self.__create('Import:', stat['total'])
                    continue
                if stage == 'rotate':
                    self.__create('Rotate:', stat['total'])
                    continue
                if stage == 'done':
                    if self.__pbar:
                        self.__pbar.finish()
                    break

            if stage == 'move' or stage == 'rotate':
                self.__pbar.update(stat[stage]['processed'])


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("echo", help="echo the string you use here")
    return parser.parse_args()


def main():
    # args = args_parse()

    log.initLogger('log.txt')

    imp = importer.Importer(config.Config(), sys.argv[1], sys.argv[2])
    pbar = ProgressBar(imp)
    imp.start()
    pbar.start()
    imp.join()
    pbar.join()


if __name__ == '__main__':
    main()
