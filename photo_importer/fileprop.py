#!/usr/bin/python3
# pylint: disable=too-many-arguments

import os
import re
import stat
import time
import logging
import datetime
import exiftool


IGNORE = 0
IMAGE = 1
VIDEO = 2
AUDIO = 3
GARBAGE = 4


class FileProp:
    DATE_REGEX = [
        (
            re.compile(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d_%H-%M-%S',
        ),
        (
            re.compile(r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'),
            '%Y-%m-%d-%H-%M-%S',
        ),
        (
            re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}.\d{2}.\d{2}'),
            '%Y-%m-%dT%H.%M.%S',
        ),
        (
            re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
            '%Y-%m-%dT%H:%M:%S',
        ),
        (
            re.compile(r'\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}'),
            '%Y_%m_%d_%H_%M_%S',
        ),
        (re.compile(r'\d{8}_\d{6}'), '%Y%m%d_%H%M%S'),
        (re.compile(r'\d{14}'), '%Y%m%d%H%M%S'),
        (re.compile(r'\d{8}'), '%Y%m%d'),
    ]

    SPACE_REGEX = re.compile(r'\s+')

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

    DATE_TAGS = [
        'EXIF:DateTimeOriginal',
        'H264:DateTimeOriginal',
        'QuickTime:MediaCreateDate',
        'PDF:CreateDate',
        'XMP:CreateDate',
        'EXIF:CreateDate',
    ]

    def __init__(self, conf):
        self.__config = conf
        self.__prepare_ext_to_type()
        self.__out_list = set()
        self.__exiftool = exiftool.ExifToolHelper()

    def __del__(self):
        self.__exiftool.terminate()

    def __prepare_ext_to_type(self):
        self.ext_to_type = {}
        for tp, cfg in self.FILE_EXT_CFG.items():
            for ext in self.__config['main'][cfg].split(','):
                ext = '.' + ext.lower()
                if ext in self.ext_to_type:
                    logging.fatal('Double ext: %s', ext)
                self.ext_to_type[ext] = tp

    def __type_by_ext(self, ext):
        try:
            return self.ext_to_type[ext]
        except KeyError:
            logging.warning('Unknown ext: %s', ext)
            return IGNORE

    def __time(self, fullname, name, tp):
        if tp not in (IMAGE, VIDEO, AUDIO):
            return None

        for src in self.__config['main'][self.TIME_SRC_CFG[tp]].split(','):
            ftime = None
            if src == 'exif':
                ftime = self.__time_by_exif(fullname)
            elif src == 'name':
                ftime = self.__time_by_name(name)
            elif src == 'attr':
                ftime = self.__time_by_attr(fullname)
            else:
                raise UserWarning(f'Wrong time_src: {src}')

            if ftime:
                return ftime

        return None

    def __time_by_name(self, fname):
        for exp, fs in self.DATE_REGEX:
            mat = exp.findall(fname)
            if len(mat):
                try:
                    ftime = datetime.datetime.strptime(mat[0], fs)
                    if ftime.year < 1990 or ftime.year > 2100:
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

            logging.warning('time by exif (%s) not found tags count: %s', fullname, len(metadata))
            for tag, val in metadata.items():
                logging.debug('%s: %s', tag, val)
        except Exception as ex:
            logging.warning('time by exif (%s) exception: %s', fullname, ex)
        return None

    def __time_by_attr(self, fullname):
        try:
            return datetime.datetime.fromtimestamp(
                time.mktime(time.localtime(os.stat(fullname)[stat.ST_MTIME]))
            )
        except (FileNotFoundError, KeyError) as ex:
            logging.warning('time by attr (%s) exception: %s', fullname, ex)
        return None

    def __calc_orig_name(self, fname):
        if not int(self.__config['main']['add_orig_name']):
            return ''
        for exp, _ in self.DATE_REGEX:
            mat = exp.findall(fname)
            if len(mat):
                return ''
        return '_' + self.SPACE_REGEX.sub('_', fname)

    def out_name_full(self, path, out_name, ext):
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
        ext = ext.lower()

        tp = self.__type_by_ext(ext)

        ftime = self.__time(fullname, fname, tp)
        time_shift = self.__config['main']['time_shift']
        if ftime and time_shift:
            ftime += datetime.timedelta(seconds=int(time_shift))

        if ftime:
            out_name = ftime.strftime(
                self.__config['main']['out_time_format']
            ) + self.__calc_orig_name(fname)
        else:
            out_name = None

        if out_name:
            ok = fname[0 : len(out_name)] == out_name
        else:
            ok = False

        return FilePropRes(self, tp, ftime, path, ext, out_name, ok)


class FilePropRes:
    def __init__(self, prop_ptr, tp, ftime, path, ext, out_name, ok):
        self.__prop_ptr = prop_ptr
        self.__type = tp
        self.__time = ftime
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

        return self.__prop_ptr.out_name_full(path, self.__out_name, self.__ext)


if __name__ == '__main__':
    import sys

    sys.path.insert(0, os.path.abspath('..'))

    from photo_importer import log
    from photo_importer import config

    log.init_logger(None, logging.DEBUG)

    fp = FileProp(config.Config()).get(sys.argv[1])
    print(fp.type(), fp.time(), fp.ok())
