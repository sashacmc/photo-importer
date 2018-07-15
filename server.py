#!/usr/bin/python3

import os
import re
import cgi
import json
import logging
import argparse
import http.server

import log
import config


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

    def __mount_get_list(self):
        dev_list = os.listdir('/dev')
        res = []
        for dev in dev_list:
            if re.match(self.server.remote_drive_reg(), dev):
                res.append(dev)
        return res

    def __mount_mount(self, dev):
        if dev == '':
            self.__bad_request_response('empty "d" param')
            return None
        logging.info('pmount')
        return os.system('pmount --umask=000 /dev/%s' % dev)

    def __mount_umount(self, dev):
        if dev == '':
            self.__bad_request_response('empty "d" param')
            return None
        logging.info('pumount')
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

        if action == 'list':
            result = self.__mount_get_list()
        elif action == 'mount':
            result = self.__mount_mount(dev)
        elif action == 'umount':
            result = self.__mount_umount(dev)
        else:
            self.__bad_request_response('unknown action %s' % action)
            return

        if result:
            self.__ok_response(result)

    def __file_request(self, path):
        try:
            fname = os.path.join(self.server.work_dir(), path)
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
        logging.info('do_GET' + self.path)
        try:
            path, params = self.__path_params()
            if path == '/mount':
                self.__mount_request(params)
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
        logging.info('do_POST' + self.path)
        try:
            path, params = self.__path_params()

            if self.path == '/mount':
                self.__mount_request(params)
                return
        except Exception as ex:
            self.__server_error_response(str(ex))
            logging.exception(ex)


class PhotoImporterServer(http.server.HTTPServer):
    def __init__(self, cfg):
        self.__cfg = cfg
        port = int(cfg['server']['port'])
        self.__work_dir = cfg['server']['work_dir']
        self.__remote_drive_reg = cfg['server']['remote_drive_reg']
        super().__init__(('', port), PhotoImporterHandler)

    def work_dir(self):
        return self.__work_dir

    def remote_drive_reg(self):
        return self.__remote_drive_reg


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
