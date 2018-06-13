#!/usr/bin/python3

import os
import logging
import threading

import mover
import config
import rotator
import fileprop


class Importer(threading.Thread):
    def __init__(self, config, input_path, output_path, dryrun):
        threading.Thread.__init__(self)
        self.__config = config
        self.__input_path = input_path
        self.__output_path = output_path
        self.__dryrun = dryrun
        self.__mov = None
        self.__rot = None
        self.__stat = {'stage': ''}

    def run(self):
        logging.info(
            'Start: %s -> %s (dryrun: %s)' %
            (self.__input_path, self.__output_path, self.__dryrun))

        filenames, dirs = self.__scan_files(self.__input_path)

        new_filenames = self.__image_filenames(self.__move_files(filenames))

        if self.__config['main']['remove_empty_dirs']:
            self.__remove_empty_dirs(dirs)

        self.__rotate_files(new_filenames)

        self.__stat['stage'] = 'done'
        logging.info('Done')

    def __scan_files(self, input_path):
        self.__stat['stage'] = 'scan'
        res_dir = []
        res = []
        for root, dirs, files in os.walk(
                input_path, onerror=self.__on_walk_error):

            for fname in files:
                res.append(os.path.join(root, fname))

            for dname in dirs:
                res_dir.append(os.path.join(root, dname))

        self.__stat['total'] = len(res)
        res.sort()
        res_dir.sort()
        logging.info('Found %i files and %i dirs' % (len(res), len(res_dir)))
        return res, res_dir

    def __on_walk_error(self, err):
        logging.error('Scan files error: %s' % err)

    def __move_files(self, filenames):
        logging.info('Moving')
        self.__mov = mover.Mover(
            self.__config,
            self.__input_path,
            self.__output_path,
            filenames,
            self.__dryrun)
        self.__stat['stage'] = 'move'

        res = self.__mov.run()
        logging.info('Processed %s files' % len(res))
        return res

    def __image_filenames(self, move_result):
        res = []
        for old, new, prop in move_result:
            if prop.type() == fileprop.IMAGE:
                res.append(new)
        return res

    def __rotate_files(self, filenames):
        logging.info('Rotating')
        self.__rot = rotator.Rotator(
            self.__config,
            filenames,
            self.__dryrun)
        self.__stat['stage'] = 'rotate'

        self.__rot.run()

    def __remove_empty_dirs(self, dirs):
        logging.info('Removing empty dirs')
        len_dirs = reversed(sorted([(len(d), d) for d in dirs]))
        for l, d in len_dirs:
            try:
                os.rmdir(d)
                logging.info('Removed: %s', d)
            except OSError:
                logging.info('Skipped: %s', d)

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
