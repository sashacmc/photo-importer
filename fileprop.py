#!/usr/bin/python3

import os
import re
import logging
import datetime


class FileProp(object):
    OTHER = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3

    EXT_TO_TYPE = {
        '.jpeg': IMAGE,
        '.jpg': IMAGE,
        '.mp4': VIDEO,
        '.mpg': VIDEO,
        '.mpeg': VIDEO,
        '.avi': VIDEO,
        '.mp3': AUDIO,
        '.3gpp': AUDIO,
        '.m4a': AUDIO
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

    def __init__(self, config, fullname, exif_prior=True):
        self.__config = config

        path, fname_ext = os.path.split(fullname)
        fname, ext = os.path.splitext(fname_ext)

        self.__type = self.__type_by_ext(ext)

        if self.__type == self.IMAGE:
            if exif_prior:
                self.__time = self.__time_by_exif(fullname)
                if self.__time is None:
                    self.__time = self.__time_by_name(fname)
            else:
                self.__time = self.__time_by_name(fname)
                if self.__time is None:
                    self.__time = self.__time_by_exif(fullname)
        else:
            self.__time = self.__time_by_name(fname)

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
