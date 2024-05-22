#!/usr/bin/python3

import os
import configparser


class Config(object):
    DEFAULT_CONFIG_FILES = (
        os.path.expanduser('~/.photo-importer.cfg'),
        '/etc/photo-importer.cfg',
    )
    DEFAULTS = {
        'main': {
            'out_time_format': '%%Y-%%m-%%d_%%H-%%M-%%S',
            'out_date_format': '%%Y/%%Y-%%m-%%d',
            'out_subdir_image': 'Foto',
            'out_subdir_video': 'Video',
            'out_subdir_audio': 'Audio',
            'time_src_image': 'exif,name',
            'time_src_video': 'exif,name,attr',
            'time_src_audio': 'exif,name,attr',
            'file_ext_image': 'jpeg,jpg',
            'file_ext_video': 'mp4,mpg,mpeg,mov,avi,mts,m2ts,3gp,m4v',
            'file_ext_audio': 'mp3,3gpp,m4a,wav,aac',
            'file_ext_garbage': 'thm,ctg',
            'file_ext_ignore': 'ini,zip,db',
            'remove_garbage': 1,
            'remove_empty_dirs': 1,
            'move_mode': 1,
            'threads_count': 2,
            'umask': '0o000',
            'use_jpegtran': 0,
            'use_shutil': 0,
            'add_orig_name': 0,
            'time_shift': 0,
        },
        'server': {
            'port': 8080,
            'web_path': 'web',
            'out_path': '/mnt/multimedia/NEW/',
            'in_path': '',
            'log_file': 'photo-importer-server.log',
        },
    }

    def __init__(self, filename=None, create=False):
        if filename is None:
            for f in self.DEFAULT_CONFIG_FILES:
                if os.path.exists(f):
                    filename = f

        self.__config = configparser.ConfigParser()
        self.__config.read_dict(self.DEFAULTS)

        if filename is not None:
            self.__config.read(
                [
                    filename,
                ]
            )

        if create:
            self.__create_if_not_exists()

    def __create_if_not_exists(self):
        if os.path.exists(self.DEFAULT_CONFIG_FILES[0]):
            return

        with open(self.DEFAULT_CONFIG_FILES[0], 'w') as conffile:
            self.__config.write(conffile)

    def __getitem__(self, sect):
        return self.__config[sect]

    def set(self, sect, name, val):
        self.__config[sect][name] = val


if __name__ == "__main__":
    Config(create=True)
