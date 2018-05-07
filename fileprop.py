#!/usr/bin/python3

import datetime


class FileProp(object):
    OTHER = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3

    def __init__(self, config, filename):
        self.__type = self.IMAGE
        self.__time = None
        self.__ok = False

        # self.__time = datetime.datetime(2000, 1, 0)

    def type(self):
        return self.__type

    def time(self):
        return self.__time

    def ok(self):
        return self.__ok
