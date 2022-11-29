#!/usr/bin/python3

import os
import re
import glob
import json
import psutil
import urllib
import logging
import argparse
import http.server
from http import HTTPStatus

from . import log
from . import config
from . import importer


FIXED_IN_PATH_NAME = 'none'


class HTTPError(Exception):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason

    def __str__(self):
        return str(self.code) + ': ' + str(self.reason)


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

    def __error_response(self, code, err):
        self.send_error(code, explain=str(err))

    def __get_mounted_list(self):
        return {
            os.path.basename(dp.device): (dp.device, dp.mountpoint)
            for dp in psutil.disk_partitions()
        }

    def __bytes_to_gbytes(self, b):
        return round(b / 1024.0 / 1024.0 / 1024.0, 2)

    def __get_removable_devices_posix(self):
        mount_list = self.__get_mounted_list()
        res = {}
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
                if pdev in mount_list:
                    res[pdev] = {
                        'dev_path': mount_list[pdev][0],
                        'mount_path': mount_list[pdev][1],
                        'read_only': read_only,
                    }
                else:
                    res[pdev] = {
                        'dev_path': '/dev/' + pdev,
                        'mount_path': '',
                        'read_only': read_only,
                    }

        return res

    def __get_removable_devices_win(self):
        import win32api
        import win32con
        import win32file

        res = {}
        for d in win32api.GetLogicalDriveStrings().split('\x00'):
            if d and win32file.GetDriveType(d) == win32con.DRIVE_REMOVABLE:
                dev_name = FIXED_IN_PATH_NAME + d
                res[dev_name] = {
                    'dev_path': dev_name,
                    'mount_path': d,
                    'read_only': not os.access(d, os.W_OK),
                }
        return res

    def __get_removable_devices(self):
        res = {}
        if os.name == 'nt':
            res = self.__get_removable_devices_win()
        elif os.name == 'posix':
            res = self.__get_removable_devices_posix()
        else:
            raise Exception('Unsupported os: %s' % os.name)

        if self.server.fixed_in_path() != '':
            res[FIXED_IN_PATH_NAME] = {
                'dev_path': FIXED_IN_PATH_NAME,
                'mount_path': self.server.fixed_in_path(),
                'read_only': not os.access(
                    self.server.fixed_in_path(), os.W_OK
                ),
            }

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
        dev_list = self.__get_removable_devices()

        res = {}
        for dev, info in dev_list.items():
            r = {}
            r['path'] = info['mount_path']
            r['progress'] = 0
            r['read_only'] = info['read_only']
            r['allow_start'] = not (
                info['read_only'] and self.server.move_mode()
            )
            if r['path']:
                stat = self.server.import_status(r['path'])
                du = psutil.disk_usage(r['path'])
                if dev == FIXED_IN_PATH_NAME:
                    r['size'] = self.__bytes_to_gbytes(
                        self.__folder_size(r['path'])
                    )
                else:
                    r['size'] = self.__bytes_to_gbytes(du.total)
                r['usage'] = du.percent
                if stat:
                    stage = stat['stage']
                    r['state'] = stage
                    if stage == 'move' or stage == 'rotate':
                        r['progress'] = round(
                            100.0 * stat[stage]['processed'] / stat['total']
                        )
                    elif stage == 'done':
                        cerr = (
                            stat['move']['errors'] + stat['rotate']['errors']
                        )
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

    def __check_dev_for_mount(self, dev):
        if dev == '':
            raise HTTPError(HTTPStatus.BAD_REQUEST, 'empty "d" param')
        dev_list = self.__get_removable_devices()
        if dev not in dev_list:
            raise HTTPError(HTTPStatus.BAD_REQUEST, 'wrong device: %s' % dev)
        device = dev_list[dev]
        if device['mount_path']:
            self.server.import_done(device['mount_path'])
        return device['dev_path']

    def __mount_mount(self, dev):
        dev_path = self.__check_dev_for_mount(dev)
        logging.debug('pmount %s', dev_path)
        return os.system('pmount --umask=000 %s' % dev_path)

    def __mount_umount(self, dev):
        dev_path = self.__check_dev_for_mount(dev)
        logging.debug('pumount %s', dev_path)
        return os.system('pumount %s' % dev_path)

    def __mount_request(self, params):
        try:
            action = params['a'][0]
        except Exception as ex:
            logging.exception(ex)
            raise HTTPError(HTTPStatus.BAD_REQUEST, str(ex))

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
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, 'unknown action %s' % action
            )

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
            logging.exception(ex)
            raise HTTPError(HTTPStatus.BAD_REQUEST, str(ex))

        try:
            out_path = params['o'][0]
        except Exception:
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
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, 'unknown action %s' % action
            )

    def __sysinfo_request(self, params):
        try:
            path = params['p'][0]
        except Exception:
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
            fname = os.path.normpath(
                os.path.join(self.server.web_path(), path)
            )
            if not fname.startswith(self.server.web_path()):
                logging.warning('incorrect path: ' + path)
                raise HTTPError(HTTPStatus.NOT_FOUND, path)
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
            with open(fname, 'rb') as f:  # lgtm[py/path-injection]
                self.send_response(200)
                self.send_header('Content-type', cont)
                self.end_headers()
                self.wfile.write(bytearray(f.read()))
        except IOError as ex:
            logging.exception(ex)
            raise HTTPError(HTTPStatus.NOT_FOUND, path)

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

            ext = os.path.splitext(path)[1]
            if ext in ('.html', '.js', '.png'):
                self.__file_request(path)
                return

            logging.warning('Wrong path: ' + path)
            raise HTTPError(HTTPStatus.NOT_FOUND, path)
        except HTTPError as ex:
            self.__error_response(ex.code, ex.reason)
        except Exception as ex:
            self.__error_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(ex))
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
        except HTTPError as ex:
            self.__error_response(ex.code, ex.reason)
        except Exception as ex:
            self.__error_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(ex))
            logging.exception(ex)


class PhotoImporterServer(http.server.HTTPServer):
    def __init__(self, cfg):
        self.__cfg = cfg
        self.__importers = {}
        port = int(cfg['server']['port'])
        self.__web_path = os.path.normpath(cfg['server']['web_path'])
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

        self.__importers[in_path] = importer.Importer(
            self.__cfg, in_path, out_path, False
        )

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
