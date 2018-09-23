#!/usr/bin/python3

import os
import re
import cgi
import json
import psutil
import logging
import argparse
import http.server

import log
import config
import importer


class PhotoImporterHandler(http.server.BaseHTTPRequestHandler):
    def __ok_response(self, result):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytearray(json.dumps(result), 'utf-8'))

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

    def __mount_get_list(self):
        mount_list = self.__get_mounted_list()
        dev_list = os.listdir('/dev')
        res = {}
        for dev in dev_list:
            if re.match(self.server.remote_drive_reg(), dev):
                r = {}
                r['path'] = mount_list.get('/dev/' + dev, '')
                r['progress'] = 0
                if r['path']:
                    stat = self.server.import_status(r['path'])
                    du = psutil.disk_usage(r['path'])
                    r['size'] = self.__bytes_to_gbytes(du.total)
                    r['usage'] = du.percent
                    if stat:
                        stage = stat['stage']
                        r['state'] = stage
                        if stage == 'move' or stage == 'rotate':
                            r['progress'] = \
                                round(100. *
                                      stat[stage]['processed'] / stat['total'])
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
        logging.info('pmount')
        path = self.__get_mounted_list().get('/dev/' + dev, None)
        if path:
            self.server.import_done(path)
        return os.system('pmount --umask=000 /dev/%s' % dev)

    def __mount_umount(self, dev):
        if dev == '':
            self.__bad_request_response('empty "d" param')
            return None
        logging.info('pumount')
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
        except:
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

    def __import_start(self, in_path):
        self.server.import_start(in_path)
        return True

    def __import_stop(self, dev):
        pass

    def __import_request(self, params):
        try:
            action = params['a'][0]
        except Exception as ex:
            self.__bad_request_response(str(ex))
            logging.exception(ex)
            return

        try:
            in_path = params['p'][0]
        except:
            self.__bad_request_response(str(ex))
            logging.exception(ex)
            return

        result = None

        if action == 'start':
            result = self.__import_start(in_path)
        elif action == 'stop':
            result = self.__import_stop(in_path)
        else:
            self.__bad_request_response('unknown action %s' % action)
            return

        self.__ok_response(result)

    def __sysinfo_request(self, params):
        res = {}
        du = psutil.disk_usage(self.server.out_path())
        mem = psutil.virtual_memory()
        res['disk_size'] = self.__bytes_to_gbytes(du.total)
        res['disk_usage'] = du.percent
        res['cpu'] = psutil.cpu_percent()
        res['mem_total'] = self.__bytes_to_gbytes(mem.total)
        res['mem_usage'] = mem.percent
        self.__ok_response(res)

    def __file_request(self, path):
        try:
            fname = os.path.join(self.server.web_path(), path)
            with open(fname) as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytearray(f.read(), 'utf-8'))
        except IOError:
            self.__not_found_response()

    def __path_params(self):
        path_params = self.path.split('?')
        if len(path_params) > 1:
            return path_params[0], cgi.parse_qs(path_params[1])
        else:
            return path_params[0], {}

    def do_GET(self):
        logging.info('do_GET: ' + self.path)
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
                self.__not_found_response()
                return

            ext = os.path.splitext(path)[1]
            if ext in ('.html', '.js') or path:
                self.__file_request(path)
                return

            logging.waring('Wrong path: ' + path)
            self.__not_found_response()
        except Exception as ex:
            self.__server_error_response(str(ex))
            logging.exception(ex)

    def do_POST(self):
        logging.info('do_POST: ' + self.path)
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
        self.__remote_drive_reg = cfg['server']['remote_drive_reg']
        self.__out_path = cfg['server']['out_path']
        super().__init__(('', port), PhotoImporterHandler)

    def web_path(self):
        return self.__web_path

    def remote_drive_reg(self):
        return self.__remote_drive_reg

    def out_path(self):
        return self.__out_path

    def import_start(self, in_path):
        logging.info('import_start: %s', in_path)
        if in_path in self.__importers:
            raise Exception('Already started')

        self.__importers[in_path] = importer.Importer(
            self.__cfg,
            in_path,
            self.out_path(),
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


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file')
    parser.add_argument('-l', '--logfile', help='Log file', default='slog.txt')
    return parser.parse_args()


def main():
    args = args_parse()

    cfg = config.Config(args.config)

    log.initLogger(args.logfile)

    try:
        server = PhotoImporterServer(cfg)
        logging.info("Photo importer server up.")
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        logging.info("Photo importer server down.")


if __name__ == '__main__':
    main()
