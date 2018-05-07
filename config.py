#!/usr/bin/python3

import configparser
import os


class Config(object):
    DEFAULT_CONFIG_FILE = os.path.expanduser('~/.photo-importer.cfg')
    DEFAULTS = {
        'main': {
            'out_time_format': '%%Y-%%m-%%d_%%H-%%M-%%S'
        }
    }

    def __init__(self, create=False):
        self.__config = configparser.ConfigParser()
        self.__config.read_dict(self.DEFAULTS)
        self.__config.read([
            'photo-importer.cfg',
            '/etc/photo-importer.cfg',
            self.DEFAULT_CONFIG_FILE])

        if create:
            self.__create_if_not_exists()

    def __create_if_not_exists(self):
        if os.path.exists(self.DEFAULT_CONFIG_FILE):
            return

        with open(self.DEFAULT_CONFIG_FILE, 'w') as conffile:
            self.__config.write(conffile)

    def __getitem__(self, sect):
        return self.__config[sect]


if __name__ == "__main__":
    Config(True)
