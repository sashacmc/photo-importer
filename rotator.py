#!/usr/bin/python3

import logging
import subprocess
import concurrent.futures

import config


class Rotator(object):
    def __init__(self, config, filenames):
        self.__config = config
        self.__filenames = filenames
        self.__processed = 0
        self.__good = 0
        self.__errors = 0

    def run(self):
        tc = int(self.__config['main']['threads_count'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=tc) as executor:

            futures = {
                executor.submit(self.__process, fn):
                fn for fn in self.__filenames}

            for future in concurrent.futures.as_completed(futures):
                self.__processed += 1
                if future.result():
                    self.__good += 1
                else:
                    self.__errors += 1

    def __process(self, filename):
        ok = False
        try:
            cmd = 'exiftran -aip "%s"' % filename
            p = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).stderr

            error = ''
            while 1:
                line = p.readline().decode("utf-8")
                if not line:
                    break

                if line.startswith('processing '):
                    ok = True
                else:
                    ok = False
                    error += line

            if error != '':
                logging.error('exiftran (%s) error: %s' % (filename, error))

        except Exception as ex:
            logging.error('Rotator exception (%s): %s' % (filename, ex))

        return ok

    def status(self):
        return {
            'total': len(self.__filenames),
            'processed': self.__processed,
            'good': self.__good,
            'errors': self.__errors}


if __name__ == '__main__':
    import sys

    rot = Rotator(config.Config(), sys.argv[1:])
    rot.run()

    print(rot.status())
