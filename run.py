#!/usr/bin/python3

import log
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
            stat = self.__imp.status()

            if stage != stat['stage']:
                stage = stat['stage']
                if stage == 'scan':
                    print('Scan... ', end='', flush=True)
                    continue
                if stage == 'move':
                    print('Done.')
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
    parser.add_argument('in_path', help="Input path")
    parser.add_argument('out_path', help="Output path", nargs='?')
    parser.add_argument('-c', '--config', help="Config file")
    parser.add_argument('-l', '--logfile', help="Log file", default='log.txt')
    return parser.parse_args()


def main():
    args = args_parse()

    cfg = config.Config(args.config)

    log.initLogger(args.logfile)

    imp = importer.Importer(
        cfg,
        args.in_path,
        args.out_path)

    pbar = ProgressBar(imp)
    imp.start()
    pbar.start()
    imp.join()
    pbar.join()


if __name__ == '__main__':
    main()
