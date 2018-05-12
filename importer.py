#!/usr/bin/python3

import os
import logging
import threading

import mover
import config
import rotator


class Importer(threading.Thread):
    def __init__(self, config, input_path, output_path):
        threading.Thread.__init__(self)
        self.__config = config
        self.__input_path = input_path
        self.__output_path = output_path
        self.__rot = None
        self.__stat = {'stage': ''}

    def run(self):
        logging.info(
            'Start: %s -> %s' %
            (self.__input_path, self.__output_path))

        self.__stat['stage'] = 'scan'
        filenames = self.__scan_files(self.__input_path)
        logging.info('Found %s files' % len(filenames))

        self.__stat['stage'] = 'move'
        new_filenames = self.__move_files(filenames)
        logging.info('Processed %s files' % len(new_filenames))

        self.__stat['stage'] = 'rotate'
        self.__rotate_files(new_filenames)

        self.__stat['stage'] = 'done'
        logging.info('Done')

    def __scan_files(self, input_path):
        res = []
        for root, dirs, files in os.walk(
                input_path, onerror=self.__on_walk_error):

            for fname in files:
                res.append(os.path.join(root, fname))

        self.__stat['total'] = len(res)
        return res

    def __on_walk_error(self, err):
        logging.error('Scan files error: %s' % err)

    def __move_files(self, filenames):
        self.__mov = mover.Mover(
            self.__config,
            self.__input_path,
            self.__output_path,
            filenames)

        return self.__mov.run()

    def __rotate_files(self, filenames):
        self.__rot = rotator.Rotator(
            self.__config,
            filenames)

        self.__rot.run()

    def status(self):
        if self.__mov:
            self.__stat['move'] = self.__mov.status()

        if self.__rot:
            self.__stat['rotate'] = self.__rot.status()

        return self.__stat


if __name__ == '__main__':
    import sys
    import log

    log.initLogger()

    imp = Importer(config.Config(), sys.argv[1], sys.argv[2])
    imp.start()
    imp.join()

    print(imp.status())
