#!/usr/bin/python3

import os
import shutil
import logging
import subprocess

from . import fileprop


class Mover(object):
    OUT_SUBDIR_CFG = {
        fileprop.IMAGE: 'out_subdir_image',
        fileprop.VIDEO: 'out_subdir_video',
        fileprop.AUDIO: 'out_subdir_audio',
    }

    def __init__(self, config, input_path, output_path, filenames, dryrun):
        self.__config = config
        self.__input_path = input_path
        self.__output_path = output_path
        self.__filenames = filenames
        self.__dryrun = dryrun
        self.__move_mode = int(config['main']['move_mode'])
        self.__remove_garbage = int(config['main']['remove_garbage'])
        self.__umask = int(config['main']['umask'], 8)
        self.__use_shutil = int(config['main']['use_shutil'])
        self.__stat = {'total': len(filenames)}
        self.__file_prop = fileprop.FileProp(self.__config)

    def run(self):
        os.umask(self.__umask)
        self.__stat['moved'] = 0
        self.__stat['copied'] = 0
        self.__stat['removed'] = 0
        self.__stat['skipped'] = 0
        self.__stat['processed'] = 0
        self.__stat['errors'] = 0
        res = []
        for fname in self.__filenames:
            try:
                prop = self.__file_prop.get(fname)
                new_fname = self.__move_file(fname, prop)
                if new_fname:
                    res.append((fname, new_fname, prop))
            except Exception as ex:
                logging.error('Move files exception: %s' % ex)
                self.__stat['errors'] += 1

            self.__stat['processed'] += 1

        return res

    def __move_file(self, fname, prop):
        if prop.type() == fileprop.GARBAGE:
            if self.__remove_garbage:
                if not self.__dryrun:
                    os.remove(fname)
                logging.info('removed "%s"' % fname)
                self.__stat['removed'] += 1
            else:
                self.__stat['skipped'] += 1
            return None

        if prop.type() == fileprop.IGNORE or prop.time() is None:
            self.__stat['skipped'] += 1
            return None

        if self.__output_path:
            path = prop.time().strftime(
                os.path.join(
                    self.__output_path,
                    self.__config['main'][self.OUT_SUBDIR_CFG[prop.type()]],
                    self.__config['main']['out_date_format'],
                )
            )

            if not os.path.isdir(path):
                if not self.__dryrun:
                    os.makedirs(path)
                logging.info('dir "%s" created' % path)

            fullname = prop.out_name_full(path)
            if self.__move_mode:
                self.__move(fname, fullname)
                logging.info('"%s" moved "%s"' % (fname, fullname))
                self.__stat['moved'] += 1
            else:
                self.__copy(fname, fullname)
                logging.info('"%s" copied "%s"' % (fname, fullname))
                self.__stat['copied'] += 1

            return fullname
        else:
            if prop.ok():
                self.__stat['skipped'] += 1
                return None
            else:
                new_fname = prop.out_name_full()
                if not self.__dryrun:
                    os.rename(fname, new_fname)
                logging.info('"%s" renamed "%s"' % (fname, new_fname))
                self.__stat['moved'] += 1
                return new_fname

    def __move(self, src, dst):
        if self.__use_shutil:
            shutil.move(src, dst)
        else:
            if not self.__run(["mv", src, dst]):
                raise SystemError('mv "%s" "%s" failed' % (src, dst))

    def __copy(self, src, dst):
        if self.__use_shutil:
            shutil.copy2(src, dst)
        else:
            if not self.__run(["cp", "-a", src, dst]):
                raise SystemError('mv "%s" "%s" failed' % (src, dst))

    def __run(self, args):
        if self.__dryrun:
            return True

        with subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            proc.wait()
            info = proc.stdout.read().strip()
            if info:
                logging.info(info.decode("utf-8"))
            err = proc.stderr.read().strip()
            if err:
                logging.error(err.decode("utf-8"))
            elif proc.returncode != 0:
                logging.error(
                    '%s failed with code %i' % (args[0], proc.returncode)
                )
            return proc.returncode == 0

    def status(self):
        return self.__stat
