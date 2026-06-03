#!/usr/bin/python3
# pylint: disable=redefined-outer-name,unused-argument,too-few-public-methods

import sys
import json
import http.client
import threading

import pytest

from photo_importer import server


class _Stream:
    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        return self._lines.pop(0) if self._lines else ''


class _RecPopen:
    calls = []

    def __init__(self, args, **kwargs):
        _RecPopen.calls.append(args)
        self.stderr = _Stream([])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _ErrPopen:
    def __init__(self, args, **kwargs):
        self.stderr = _Stream(['mount error\n'])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


_DEVICES_ATTR = '_PhotoImporterHandler__get_removable_devices'


@pytest.fixture
def http_server(tmp_path, cfg, fake_exiftool, monkeypatch):
    web = tmp_path / 'web'
    web.mkdir()
    (web / 'index.html').write_text('<html>hello</html>')
    (web / 'app.js').write_text('console.log(1)')
    cfg.set('server', 'web_path', str(web))
    cfg.set('server', 'host', '127.0.0.1')
    cfg.set('server', 'port', '0')
    monkeypatch.setattr(server.PhotoImporterHandler, 'log_message', lambda *a, **k: None)

    srv = server.PhotoImporterServer(cfg)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield srv.server_port
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join()


def _request(port, method, path):
    conn = http.client.HTTPConnection('127.0.0.1', port)
    try:
        conn.request(method, path)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, resp.getheader('Content-type'), body
    finally:
        conn.close()


def test_index_served(http_server):
    status, ctype, body = _request(http_server, 'GET', '/')
    assert status == 200
    assert ctype == 'text/html'
    assert b'hello' in body


def test_js_content_type(http_server):
    status, ctype, _ = _request(http_server, 'GET', '/app.js')
    assert status == 200
    assert ctype == 'application/javascript'


def test_missing_file_404(http_server):
    status, _, _ = _request(http_server, 'GET', '/nope.html')
    assert status == 404


def test_path_traversal_blocked(http_server, tmp_path):
    (tmp_path / 'secret.html').write_text('secret')
    status, _, _ = _request(http_server, 'GET', '/../secret.html')
    assert status == 404


def test_unknown_get_path_404(http_server):
    status, _, _ = _request(http_server, 'GET', '/bogus')
    assert status == 404


def test_unknown_post_path_404(http_server):
    status, _, _ = _request(http_server, 'POST', '/bogus')
    assert status == 404


def test_sysinfo(http_server, tmp_path):
    status, _, body = _request(http_server, 'GET', '/sysinfo?p=' + str(tmp_path))
    assert status == 200
    data = json.loads(body)
    assert {'disk_size', 'disk_usage', 'cpu', 'mem_total', 'mem_usage'} <= set(data)


def test_mount_list_empty(http_server, monkeypatch):
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: {})
    status, _, body = _request(http_server, 'GET', '/mount?a=list')
    assert status == 200
    assert json.loads(body) == {}


def test_mount_unknown_action_400(http_server):
    status, _, _ = _request(http_server, 'GET', '/mount?a=frobnicate')
    assert status == 400


def test_mount_mount_uses_argv_list(http_server, monkeypatch):
    _RecPopen.calls = []
    monkeypatch.setattr(
        server.PhotoImporterHandler,
        _DEVICES_ATTR,
        lambda self: {'sdz1': {'dev_path': '/dev/sdz1', 'mount_path': '', 'read_only': False}},
    )
    monkeypatch.setattr(server.subprocess, 'Popen', _RecPopen)

    status, _, _ = _request(http_server, 'POST', '/mount?a=mount&d=sdz1')

    assert status == 200
    assert _RecPopen.calls == [['pmount', '--umask=000', '/dev/sdz1']]


def test_mount_unknown_device_400(http_server, monkeypatch):
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: {})
    status, _, _ = _request(http_server, 'POST', '/mount?a=mount&d=sdz1')
    assert status == 400


def test_mount_list_with_devices(http_server, tmp_path, monkeypatch):
    mnt = tmp_path / 'mnt'
    mnt.mkdir()
    (mnt / 'f.bin').write_bytes(b'x' * 10)
    devices = {
        'sdz1': {'dev_path': '/dev/sdz1', 'mount_path': str(mnt), 'read_only': False},
        server.FIXED_IN_PATH_NAME: {
            'dev_path': server.FIXED_IN_PATH_NAME,
            'mount_path': str(mnt),
            'read_only': False,
        },
    }
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: devices)

    status, _, body = _request(http_server, 'GET', '/mount?a=list')

    assert status == 200
    data = json.loads(body)
    assert set(data) == {'sdz1', server.FIXED_IN_PATH_NAME}
    assert data['sdz1']['state'] == 'mounted'


def test_mount_cmd_error_500(http_server, monkeypatch):
    monkeypatch.setattr(
        server.PhotoImporterHandler,
        _DEVICES_ATTR,
        lambda self: {'sdz1': {'dev_path': '/dev/sdz1', 'mount_path': '', 'read_only': False}},
    )
    monkeypatch.setattr(server.subprocess, 'Popen', _ErrPopen)

    status, _, _ = _request(http_server, 'POST', '/mount?a=umount&d=sdz1')

    assert status == 500


# --- import requests over HTTP ---


def test_import_start_over_http(http_server, tmp_path):
    indir = tmp_path / 'imp_in'
    indir.mkdir()
    status, _, body = _request(http_server, 'POST', f'/import?a=start&p={indir}&o={tmp_path / "imp_out"}')
    assert status == 200
    assert json.loads(body) is True


def test_import_getlog_over_http(http_server, tmp_path):
    indir = tmp_path / 'imp_log'
    indir.mkdir()
    _request(http_server, 'POST', f'/import?a=start&p={indir}&o={tmp_path / "o"}')
    status, ctype, _ = _request(http_server, 'GET', f'/import?a=getlog&p={indir}')
    assert status == 200
    assert ctype == 'text/plain'


def test_import_done_over_http(http_server, tmp_path):
    indir = tmp_path / 'imp_done'
    indir.mkdir()
    _request(http_server, 'POST', f'/import?a=start&p={indir}&o={tmp_path / "o"}')
    status, _, _ = _request(http_server, 'POST', f'/import?a=done&p={indir}')
    assert status == 200


def test_import_stop_not_implemented(http_server):
    status, _, body = _request(http_server, 'GET', '/import?a=stop&p=/x')
    assert status == 200
    assert json.loads(body) is False


def test_import_missing_param_400(http_server):
    status, _, _ = _request(http_server, 'GET', '/import?a=start')
    assert status == 400


def test_import_unknown_action_400(http_server):
    status, _, _ = _request(http_server, 'GET', '/import?a=foo&p=/x')
    assert status == 400


# --- mount list reflecting import status ---


def _device(mnt):
    return {'sdz1': {'dev_path': '/dev/sdz1', 'mount_path': str(mnt), 'read_only': False}}


def test_mount_list_import_progress(http_server, tmp_path, monkeypatch):
    mnt = tmp_path / 'm'
    mnt.mkdir()
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: _device(mnt))
    monkeypatch.setattr(
        server.PhotoImporterServer,
        'import_status',
        lambda self, p: {'stage': 'move', 'total': 10, 'move': {'processed': 5}},
    )

    status, _, body = _request(http_server, 'GET', '/mount?a=list')

    assert status == 200
    data = json.loads(body)
    assert data['sdz1']['state'] == 'move'
    assert data['sdz1']['progress'] == 50


def test_mount_list_import_done_with_errors(http_server, tmp_path, monkeypatch):
    mnt = tmp_path / 'm2'
    mnt.mkdir()
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: _device(mnt))
    monkeypatch.setattr(
        server.PhotoImporterServer,
        'import_status',
        lambda self, p: {
            'stage': 'done',
            'total': 3,
            'move': {'errors': 1},
            'rotate': {'errors': 0},
        },
    )

    status, _, body = _request(http_server, 'GET', '/mount?a=list')

    assert status == 200
    assert json.loads(body)['sdz1']['state'] == 'error'


def test_mount_list_import_done_ok(http_server, tmp_path, monkeypatch):
    mnt = tmp_path / 'm3'
    mnt.mkdir()
    monkeypatch.setattr(server.PhotoImporterHandler, _DEVICES_ATTR, lambda self: _device(mnt))
    monkeypatch.setattr(
        server.PhotoImporterServer,
        'import_status',
        lambda self, p: {
            'stage': 'done',
            'total': 3,
            'move': {'errors': 0},
            'rotate': {'errors': 0},
        },
    )

    status, _, body = _request(http_server, 'GET', '/mount?a=list')

    assert status == 200
    data = json.loads(body)['sdz1']
    assert data['state'] == 'done'
    assert data['total'] == 3


# --- main() ---


def test_main_handles_keyboard_interrupt(tmp_path, monkeypatch):
    cfgfile = tmp_path / 'c.cfg'
    cfgfile.write_text(f'[server]\nlog_file = {tmp_path / "s.log"}\n')

    closed = []

    class _FakeServer:
        def __init__(self, cfg):
            self.socket = type('S', (), {'close': lambda s: closed.append(True)})()

        def serve_forever(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(server, 'PhotoImporterServer', _FakeServer)
    monkeypatch.setattr(sys, 'argv', ['prog', '-c', str(cfgfile)])

    server.main()

    assert closed == [True]


def test_import_lifecycle(tmp_path, cfg, fake_exiftool):
    indir = tmp_path / 'in'
    indir.mkdir()
    cfg.set('server', 'host', '127.0.0.1')
    cfg.set('server', 'port', '0')

    srv = server.PhotoImporterServer(cfg)
    try:
        assert srv.import_status(str(indir)) is None
        srv.import_start(str(indir), str(tmp_path / 'out'))
        assert srv.import_status(str(indir)) is not None
        assert srv.get_log(str(indir)) != ''
        assert srv.import_done(str(indir)) == ''
        assert srv.import_status(str(indir)) is None
    finally:
        srv.server_close()
