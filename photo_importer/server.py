#!/usr/bin/python3

import os
import re
import sys
import glob
import json
import psutil
import urllib
import logging
import argparse
import http.server

sys.path.insert(0, os.path.abspath('..'))

from photo_importer import log  # noqa
from photo_importer import config  # noqa
from photo_importer import importer  # noqa


FIXED_IN_PATH_NAME = 'none'


class PhotoImporterHandler(http.server.BaseHTTPRequestHandler):

    def __ok_response(self, result):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytearray(json.dumps(result), 'utf-8'))

    def __text_response(self, result):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(bytearray(result, 'utf-8'))

    def __bad_request_response(self, err):
        self.send_response(400)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(bytearray(err, 'utf-8'))

    def __not_found_response(self):
        self.send_error(404, 'File Not Found: %s' % self.path)

    def __server_error_response(self, err):
        self.send_error(500, 'Internal Server Error: %s' % err)

    def __get_mounted_list(self):
        return {dp.device: dp.mountpoint for dp in psutil.disk_partitions()}

    def __bytes_to_gbytes(self, b):
        return round(b / 1024. / 1024. / 1024., 2)

    def __get_removable_devices(self):
        res = []
        for path in glob.glob('/sys/block/*/device'):
            dev = re.sub('.*/(.*?)/device', '\g<1>', path)
            with open('/sys/block/%s/removable' % (dev,)) as f:
                if f.read(1) != '1':
                    continue
            read_only = False
            with open('/sys/block/%s/ro' % (dev,)) as f:
                if f.read(1) == '1':
                    read_only = True
            for ppath in glob.glob('/sys/block/%s/%s*' % (dev, dev)):
                pdev = os.path.split(ppath)[1]
                res.append((pdev, read_only))
        return res

    def __folder_size(self, path):
        res = 0
        for entry in os.scandir(path):
            if entry.is_file():
                res += entry.stat().st_size
            elif entry.is_dir():
                res += self.__folder_size(entry.path)
        return res

    def __mount_get_list(self):
        mount_list = self.__get_mounted_list()
        dev_list = self.__get_removable_devices()

        if self.server.fixed_in_path() != '':
            mount_list['/dev/' + FIXED_IN_PATH_NAME] = \
                self.server.fixed_in_path()
            dev_list.append((
                FIXED_IN_PATH_NAME,
                not os.access(self.server.fixed_in_path(), os.W_OK)))

        res = {}
        for dev, read_only in dev_list:
            r = {}
            r['path'] = mount_list.get('/dev/' + dev, '')
            r['progress'] = 0
            r['read_only'] = read_only
            r['allow_start'] = not (read_only and self.server.move_mode())
            if r['path']:
                stat = self.server.import_status(r['path'])
                du = psutil.disk_usage(r['path'])
                if dev == FIXED_IN_PATH_NAME:
                    r['size'] = self.__bytes_to_gbytes(
                        self.__folder_size(r['path']))
                else:
                    r['size'] = self.__bytes_to_gbytes(du.total)
                r['usage'] = du.percent
                if stat:
                    stage = stat['stage']
                    r['state'] = stage
                    if stage == 'move' or stage == 'rotate':
                        r['progress'] = \
                            round(100. *
                                  stat[stage]['processed'] / stat['total'])
                    elif stage == 'done':
                        cerr = stat['move']['errors'] + \
                            stat['rotate']['errors']
                        if cerr != 0:
                            r['state'] = 'error'
                            r['total'] = cerr
                            r['details'] = str(stat)
                        else:
                            r['total'] = stat['total']
                else:
                    r['state'] = 'mounted'
            else:
                r['size'] = 0
                r['usage'] = 0
                r['state'] = 'unmounted'
            res[dev] = r
        return res

    def __mount_mount(self, dev):
        if dev == '':
            self.__bad_request_response('empty "d" param')
            return None
        logging.debug('pmount')
        path = self.__get_mounted_list().get('/dev/' + dev, None)
        if path:
            self.server.import_done(path)
        return os.system('pmount --umask=000 /dev/%s' % dev)

    def __mount_umount(self, dev):
        if dev == '':
            self.__bad_request_response('empty "d" param')
            return None
        logging.debug('pumount')
        path = self.__get_mounted_list().get('/dev/' + dev, None)
        if path:
            self.server.import_done(path)
        return os.system('pumount /dev/%s' % dev)

    def __mount_request(self, params):
        try:
            action = params['a'][0]
        except Exception as ex:
            self.__bad_request_response(str(ex))
            logging.exception(ex)
            return

        try:
            dev = params['d'][0]
        except Exception:
            dev = ''

        result = None

        if action == 'list':
            result = self.__mount_get_list()
        elif action == 'mount':
            result = self.__mount_mount(dev)
        elif action == 'umount':
            result = self.__mount_umount(dev)
        else:
            self.__bad_request_response('unknown action %s' % action)
            return

        self.__ok_response(result)

    def __import_start(self, in_path, out_path):
        self.server.import_start(in_path, out_path)
        return True

    def __import_stop(self, dev):
        pass

    def __import_get_log(self, in_path):
        return self.server.get_log(in_path)

    def __import_request(self, params):
        try:
            action = params['a'][0]
            in_path = params['p'][0]
        except Exception as ex:
            self.__bad_request_response(str(ex))
            logging.exception(ex)
            return

        try:
            out_path = params['o'][0]
        except Exception as ex:
            out_path = self.server.out_path()

        result = None

        if action == 'start':
            result = self.__import_start(in_path, out_path)
            self.__ok_response(result)
        elif action == 'stop':
            result = self.__import_stop(in_path)
            self.__ok_response(result)
        elif action == 'getlog':
            result = self.__import_get_log(in_path)
            self.__text_response(result)
        else:
            self.__bad_request_response('unknown action %s' % action)
            return

    def __sysinfo_request(self, params):
        try:
            path = params['p'][0]
        except Exception as ex:
            path = self.server.out_path()
        res = {}
        du = psutil.disk_usage(path)
        mem = psutil.virtual_memory()
        res['disk_size'] = self.__bytes_to_gbytes(du.total)
        res['disk_usage'] = du.percent
        res['cpu'] = psutil.cpu_percent()
        res['mem_total'] = self.__bytes_to_gbytes(mem.total)
        res['mem_usage'] = mem.percent
        self.__ok_response(res)

    def __file_request(self, path):
        try:
            if (path[0]) == '/':
                path = path[1:]
            fname = os.path.join(self.server.web_path(), path)
            ext = os.path.splitext(fname)[1]
            cont = ''
            if ext == '.html':
                cont = 'text/html'
            elif ext == '.js':
                cont = 'text/script'
            elif ext == '.png':
                cont = 'image/png'
            else:
                cont = 'text/none'
            with open(fname, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', cont)
                self.end_headers()
                self.wfile.write(bytearray(f.read()))
        except IOError as ex:
            self.__not_found_response()
            logging.exception(ex)

    def __path_params(self):
        path_params = self.path.split('?')
        if len(path_params) > 1:
            return path_params[0], urllib.parse.parse_qs(path_params[1])
        else:
            return path_params[0], {}

    def do_GET(self):
        logging.debug('do_GET: ' + self.path)
        try:
            path, params = self.__path_params()
            if path == '/mount':
                self.__mount_request(params)
                return

            if path == '/import':
                self.__import_request(params)
                return

            if path == '/sysinfo':
                self.__sysinfo_request(params)
                return

            if path == '/':
                path = 'index.html'

            if '..' in path:
                logging.warning('".." in path: ' + path)
                self.__not_found_response()
                return

            ext = os.path.splitext(path)[1]
            if ext in ('.html', '.js', '.png'):
                self.__file_request(path)
                return

            logging.warning('Wrong path: ' + path)
            self.__not_found_response()
        except Exception as ex:
            self.__server_error_response(str(ex))
            logging.exception(ex)

    def do_POST(self):
        logging.debug('do_POST: ' + self.path)
        try:
            path, params = self.__path_params()

            if path == '/mount':
                self.__mount_request(params)
                return

            if path == '/import':
                self.__import_request(params)
                return
        except Exception as ex:
            self.__server_error_response(str(ex))
            logging.exception(ex)


class PhotoImporterServer(http.server.HTTPServer):
    def __init__(self, cfg):
        self.__cfg = cfg
        self.__importers = {}
        port = int(cfg['server']['port'])
        self.__web_path = cfg['server']['web_path']
        self.__out_path = cfg['server']['out_path']
        self.__fixed_in_path = cfg['server']['in_path']
        self.__move_mode = int(cfg['main']['move_mode'])
        super().__init__(('', port), PhotoImporterHandler)

    def web_path(self):
        return self.__web_path

    def out_path(self):
        return self.__out_path

    def fixed_in_path(self):
        return self.__fixed_in_path

    def move_mode(self):
        return self.__move_mode

    def import_start(self, in_path, out_path):
        logging.info('import_start: %s', in_path)
        if in_path in self.__importers and in_path != self.fixed_in_path():
            raise Exception('Already started')

        self.__importers[in_path] = importer.Importer(
            self.__cfg,
            in_path,
            out_path,
            False)

        self.__importers[in_path].start()

    def import_status(self, in_path):
        if in_path in self.__importers:
            return self.__importers[in_path].status()
        else:
            return None

    def import_done(self, in_path):
        logging.info('import_done: %s', in_path)
        if in_path in self.__importers:
            del self.__importers[in_path]

    def get_log(self, in_path):
        if in_path in self.__importers:
            return self.__importers[in_path].log_text()
        else:
            return ''


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file')
    parser.add_argument('-l', '--logfile', help='Log file')
    return parser.parse_args()


def main():
    args = args_parse()

    cfg = config.Config(args.config)

    if args.logfile:
        logfile = args.logfile
    else:
        logfile = cfg['server']['log_file']

    log.initLogger(logfile)

    try:
        server = PhotoImporterServer(cfg)
        logging.info("Photo importer server up.")
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        logging.info("Photo importer server down.")


if __name__ == '__main__':
    main()
