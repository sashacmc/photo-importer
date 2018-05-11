#!/usr/bin/python3

import os
import shutil
import logging
import threading

import config
import rotator
import fileprop


class Importer(threading.Thread):
    def __init__(self, config, input_path, output_path):
        threading.Thread.__init__(self)
        self.__config = config
        self.__input_path = input_path
        self.__output_path = output_path
        self.__move_mode = int(config['main']['move_mode'])
        self.__remove_garbage = int(config['main']['remove_garbage'])
        self.__rot = None
        self.__stat = {}

    def run(self):
        logging.info(
            'Start: %s -> %s' %
            (self.__input_path, self.__output_path))

        filenames = self.__scan_files(self.__input_path)
        logging.info('Found %s files' % len(filenames))

        new_filenames = self.__move_files(filenames)
        logging.info('Moved %s files' % len(new_filenames))

        self.__rotate_files(new_filenames)
        logging.info('Done')

    def __scan_files(self, input_path):
        res = []
        for root, dirs, files in os.walk(input_path):
            for fname in files:
                res.append(os.path.join(root, fname))

        self.__stat['total'] = len(res)
        return res

    def __move_files(self, filenames):
        self.__stat['moved'] = 0
        self.__stat['copied'] = 0
        self.__stat['removed'] = 0
        self.__stat['skipped'] = 0
        self.__stat['processed'] = 0
        res = []
        for fname in filenames:
            self.__stat['processed'] += 1
            prop = fileprop.FileProp(self.__config, fname)

            if prop.type() == prop.GARBAGE:
                if self.__remove_garbage:
                    os.remove(fname)
                    self.__stat['removed'] += 1
                else:
                    self.__stat['skipped'] += 1
                continue

            if prop.type() == prop.OTHER or prop.time() is None:
                self.__stat['skipped'] += 1
                continue

            if self.__output_path:
                subdir = prop.time().strftime(
                    self.__config['main']['out_date_format'])

                path = os.path.join(self.__output_path, subdir)
                if not os.path.isdir(path):
                    os.makedirs(path)

                fullname = prop.out_name_full(path)
                if self.__move_mode:
                    shutil.move(fname, fullname)
                    self.__stat['moved'] += 1
                else:
                    shutil.copy2(fname, fullname)
                    self.__stat['copied'] += 1
                res.append(fullname)
            else:
                if prop.ok():
                    res.append(fname)
                else:
                    new_fname = prop.out_name_full()
                    os.rename(fname, new_fname)
                    res.append(new_fname)

                self.__stat['moved'] += 1

        return res

    def __rotate_files(self, filenames):
        self.__rot = rotator.Rotator(self.__config, filenames)
        self.__rot.run()

    def status(self):
        if self.__rot:
            self.__stat['rotation'] = self.__rot.status()
        return self.__stat


if __name__ == '__main__':
    import sys
    import log

    log.initLogger()

    imp = Importer(config.Config(False), sys.argv[1], sys.argv[2])
    imp.start()
    imp.join()

    print(imp.status())
