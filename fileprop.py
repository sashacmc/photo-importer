#!/usr/bin/python3

import os
import re
import stat
import time
import logging
import exifread
import datetime

import config


class FileProp(object):
    OTHER = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    GARBAGE = 4

    EXT_TO_TYPE = {
        '.jpeg': IMAGE,
        '.jpg': IMAGE,
        '.mp4': VIDEO,
        '.mpg': VIDEO,
        '.mpeg': VIDEO,
        '.avi': VIDEO,
        '.mp3': AUDIO,
        '.3gpp': AUDIO,
        '.m4a': AUDIO,
        '.thm': GARBAGE,
        '.ctg': GARBAGE,
    }

    DATE_REX = [
        (re.compile('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d_%H-%M-%S'),
        (re.compile('\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d-%H-%M-%S'),
        (re.compile('\d{4}-\d{2}-\d{2}T\d{2}.\d{2}.\d{2}'),
            '%Y-%m-%dT%H.%M.%S'),
        (re.compile('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
            '%Y-%m-%dT%H:%M:%S'),
        (re.compile('\d{8}_\d{6}'), '%Y%m%d_%H%M%S'),
        (re.compile('\d{14}'), '%Y%m%d%H%M%S'),
        (re.compile('\d{8}'), '%Y%m%d'),
    ]

    def __init__(self, config, fullname):
        self.__config = config

        self.__path, fname_ext = os.path.split(fullname)
        fname, self.__ext = os.path.splitext(fname_ext)

        self.__type = self.__type_by_ext(self.__ext)

        self.__time = self.__time(fullname, fname)

        out_name = self.out_name()
        if out_name:
            self.__ok = fname[0:len(out_name)] == out_name
        else:
            self.__ok = False

    def __type_by_ext(self, ext):
        try:
            return self.EXT_TO_TYPE[ext.lower()]
        except KeyError:
            logging.warning('Unknown ext: ' + ext)
            return self.OTHER

    def __time(self, fullname, name):
        for src in self.__config['main']['time_src'].split(','):
            time = None
            if src == 'exif':
                time = self.__time_by_exif(fullname)
            elif src == 'name':
                time = self.__time_by_name(name)
            elif src == 'attr':
                time = self.__time_by_attr(name)
            else:
                raise Exception('Wrong time_src: ' + src)

            if time:
                return time

    def __time_by_name(self, fname):
        for exp, fs in self.DATE_REX:
            mat = exp.findall(fname)
            if len(mat):
                try:
                    time = datetime.datetime.strptime(mat[0], fs)
                    if time.year < 1990 or time.year > 2100:
                        continue

                    return time
                except ValueError:
                    pass

        return None

    def __time_by_exif(self, fullname):
        if self.__type != self.IMAGE:
            return None

        try:
            with open(fullname, 'rb') as f:
                tags = exifread.process_file(f)
                strtime = tags['EXIF DateTimeOriginal'].values
                return datetime.datetime.strptime(strtime, '%Y:%m:%d %H:%M:%S')
        except (FileNotFoundError, KeyError):
            return None

    def __time_by_attr(self, fullname):
        try:
            self.__time = time.localtime(os.stat(fullname)[stat.ST_MTIME])
        except (FileNotFoundError, KeyError):
            return None

    def out_name(self):
        if self.__time:
            return self.__time.strftime(
                self.__config['main']['out_time_format'])
        else:
            return None

    def type(self):
        return self.__type

    def time(self):
        return self.__time

    def ok(self):
        return self.__ok

    def path(self):
        return self.__path

    def ext(self):
        return self.__ext

    def out_name_full(self, path=None):
        if path is None:
            path = self.__path

        return os.path.join(path, self.out_name()) + self.ext()


if __name__ == '__main__':
    import sys

    fp = FileProp(config.Config(False), sys.argv[1])
    print(fp.type(), fp.time(), fp.ok())
