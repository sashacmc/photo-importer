#!/usr/bin/python3

import os
import re
import stat
import time
import logging
import exiftool
import datetime


IGNORE = 0
IMAGE = 1
VIDEO = 2
AUDIO = 3
GARBAGE = 4


class FileProp(object):
    DATE_REGEX = [
        (
            re.compile('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d_%H-%M-%S',
        ),
        (
            re.compile('\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d-%H-%M-%S',
        ),
        (
            re.compile('\d{4}-\d{2}-\d{2}T\d{2}.\d{2}.\d{2}'),
            '%Y-%m-%dT%H.%M.%S',
        ),
        (
            re.compile('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
            '%Y-%m-%dT%H:%M:%S',
        ),
        (
            re.compile('\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}'),
            '%Y_%m_%d_%H_%M_%S',
        ),
        (re.compile('\d{8}_\d{6}'), '%Y%m%d_%H%M%S'),
        (re.compile('\d{14}'), '%Y%m%d%H%M%S'),
        (re.compile('\d{8}'), '%Y%m%d'),
    ]

    TIME_SRC_CFG = {
        IMAGE: 'time_src_image',
        VIDEO: 'time_src_video',
        AUDIO: 'time_src_audio',
    }

    FILE_EXT_CFG = {
        IMAGE: 'file_ext_image',
        VIDEO: 'file_ext_video',
        AUDIO: 'file_ext_audio',
        GARBAGE: 'file_ext_garbage',
        IGNORE: 'file_ext_ignore',
    }

    EXT_TO_TYPE = {}

    DATE_TAGS = [
        'EXIF:DateTimeOriginal',
        'H264:DateTimeOriginal',
        'QuickTime:MediaCreateDate',
        'PDF:CreateDate',
        'XMP:CreateDate',
        'EXIF:CreateDate',
    ]

    def __init__(self, config):
        self.__config = config
        self.__prepare_ext_to_type()
        self.__out_list = set()
        self.__exiftool = exiftool.ExifToolHelper()

    def __del__(self):
        self.__exiftool.terminate()

    def __prepare_ext_to_type(self):
        self.EXT_TO_TYPE = {}
        for tp, cfg in self.FILE_EXT_CFG.items():
            for ext in self.__config['main'][cfg].split(','):
                ext = '.' + ext.lower()
                if ext in self.EXT_TO_TYPE:
                    logging.fatal('Double ext: ' + ext)
                self.EXT_TO_TYPE[ext] = tp

    def __type_by_ext(self, ext):
        try:
            return self.EXT_TO_TYPE[ext.lower()]
        except KeyError:
            logging.warning('Unknown ext: ' + ext)
            return IGNORE

    def __time(self, fullname, name, tp):
        if tp not in (IMAGE, VIDEO, AUDIO):
            return None

        for src in self.__config['main'][self.TIME_SRC_CFG[tp]].split(','):
            time = None
            if src == 'exif':
                time = self.__time_by_exif(fullname)
            elif src == 'name':
                time = self.__time_by_name(name)
            elif src == 'attr':
                time = self.__time_by_attr(fullname)
            else:
                raise Exception('Wrong time_src: ' + src)

            if time:
                return time

        return None

    def __time_by_name(self, fname):
        for exp, fs in self.DATE_REGEX:
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
        try:
            metadata = self.__exiftool.get_metadata(fullname)[0]
            for tag in self.DATE_TAGS:
                if tag in metadata:
                    md = metadata[tag]
                    pos = md.find('+')
                    if pos > 0:
                        md = md[0:pos]
                    return datetime.datetime.strptime(md, '%Y:%m:%d %H:%M:%S')

            logging.warning(
                'time by exif (%s) not found tags count: %s'
                % (fullname, len(metadata))
            )
            for tag, val in metadata.items():
                logging.debug('%s: %s' % (tag, val))
            return None
        except Exception as ex:
            logging.warning('time by exif (%s) exception: %s' % (fullname, ex))

    def __time_by_attr(self, fullname):
        try:
            return datetime.datetime.fromtimestamp(
                time.mktime(time.localtime(os.stat(fullname)[stat.ST_MTIME]))
            )
        except (FileNotFoundError, KeyError) as ex:
            logging.warning('time by attr (%s) exception: %s' % (fullname, ex))

    def _out_name_full(self, path, out_name, ext):
        res = os.path.join(path, out_name) + ext

        i = 1
        while os.path.isfile(res) or res in self.__out_list:
            i += 1
            res = os.path.join(path, out_name + '_' + str(i) + ext)

        self.__out_list.add(res)

        return res

    def get(self, fullname):
        path, fname_ext = os.path.split(fullname)
        fname, ext = os.path.splitext(fname_ext)

        tp = self.__type_by_ext(ext)

        ftime = self.__time(fullname, fname, tp)

        if ftime:
            out_name = ftime.strftime(self.__config['main']['out_time_format'])
        else:
            out_name = None

        if out_name:
            ok = fname[0 : len(out_name)] == out_name
        else:
            ok = False

        return FilePropRes(self, tp, ftime, path, ext, out_name, ok)


class FilePropRes(object):
    def __init__(self, prop_ptr, tp, time, path, ext, out_name, ok):
        self.__prop_ptr = prop_ptr
        self.__type = tp
        self.__time = time
        self.__path = path
        self.__ext = ext
        self.__out_name = out_name
        self.__ok = ok

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

    def out_name(self):
        return self.__out_name

    def out_name_full(self, path=None):
        if path is None:
            path = self.__path

        return self.__prop_ptr._out_name_full(
            path, self.__out_name, self.__ext
        )


if __name__ == '__main__':
    import sys

    sys.path.insert(0, os.path.abspath('..'))

    from photo_importer import log
    from photo_importer import config

    log.initLogger(None, logging.DEBUG)

    fp = FileProp(config.Config()).get(sys.argv[1])
    print(fp.type(), fp.time(), fp.ok())
