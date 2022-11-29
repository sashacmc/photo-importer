#!/usr/bin/python3

import os
import logging
import exiftool
import tempfile
import subprocess
import concurrent.futures


JPEGTRAN_COMMAND = {
    0: None,
    1: None,
    2: '-flip horizontal',
    3: '-rotate 180',
    4: '-flip vertical',
    5: '-transpose',
    6: '-rotate 90',
    7: '-transverse',
    8: '-rotate 270',
}

ORIENTATION_TAG = 'EXIF:Orientation'


class Rotator(object):
    def __init__(self, config, filenames, dryrun):
        self.__config = config
        self.__filenames = filenames
        self.__dryrun = dryrun
        self.__processed = 0
        self.__good = 0
        self.__errors = 0

    def run(self):
        os.umask(int(self.__config['main']['umask'], 8))
        tc = int(self.__config['main']['threads_count'])
        processor = self.__process_exiftran
        self.__exiftool = None
        if int(self.__config['main']['use_jpegtran']):
            self.__exiftool = exiftool.ExifToolHelper()
            processor = self.__process_jpegtran
            tc = 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=tc) as executor:

            futures = {
                executor.submit(processor, fn): fn for fn in self.__filenames
            }

            for future in concurrent.futures.as_completed(futures):
                self.__processed += 1
                if future.result():
                    self.__good += 1
                else:
                    self.__errors += 1

        if self.__exiftool is not None:
            self.__exiftool.terminate()

    def __process_exiftran(self, filename):
        ok = False
        try:
            cmd = 'exiftran -aip "%s"' % filename
            logging.debug('rotate: %s' % cmd)

            if self.__dryrun:
                return True

            error = ''
            with subprocess.Popen(
                cmd,
                shell=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as p:
                while True:
                    line = p.stderr.readline()
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

    def __process_jpegtran(self, filename):
        try:
            orientation_cmd = self.__get_orientation_cmd(filename)
            if orientation_cmd is None:
                return True

            logging.debug(
                'rotate: jpegtran %s %s' % (orientation_cmd, filename)
            )

            if self.__dryrun:
                return True

            handle, tmpfile = tempfile.mkstemp(dir=os.path.dirname(filename))
            os.close(handle)

            cmd = 'jpegtran -copy all -outfile %s %s %s' % (
                tmpfile,
                orientation_cmd,
                filename,
            )

            with subprocess.Popen(
                cmd,
                shell=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as p:
                line = p.stderr.readline()
                if line:
                    logging.error(
                        'jpegtran (%s) failed: %s' % (filename, line)
                    )
                    return False

            self.__clear_orientation_tag(tmpfile)

            os.remove(filename)
            os.rename(tmpfile, filename)

            return True
        except Exception as ex:
            logging.error('Rotator exception (%s): %s' % (filename, ex))
            return False

    def __get_orientation_cmd(self, fullname):
        tags = self.__exiftool.get_tags(fullname, ORIENTATION_TAG)
        if ORIENTATION_TAG not in tags:
            return None
        orientation = tags[ORIENTATION_TAG]
        if 0 <= orientation and orientation < len(JPEGTRAN_COMMAND):
            return JPEGTRAN_COMMAND[orientation]
        else:
            return None

    def __clear_orientation_tag(self, fullname):
        self.__exiftool.set_tags(fullname, {ORIENTATION_TAG: 1})
        try:
            os.remove(fullname + '_original')
        except Exception:
            pass

    def status(self):
        return {
            'total': len(self.__filenames),
            'processed': self.__processed,
            'good': self.__good,
            'errors': self.__errors,
        }
