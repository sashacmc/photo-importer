#!/usr/bin/python3
# pylint: disable=redefined-outer-name,unused-argument,too-few-public-methods

import pytest

from photo_importer import rotator


class _Stream:
    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        return self._lines.pop(0) if self._lines else ''

    def read(self):
        s = ''.join(self._lines)
        self._lines = []
        return s


class _FakePopen:
    instances = []
    stderr_lines = []

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.returncode = 0
        self.stderr = _Stream(list(_FakePopen.stderr_lines))
        self.stdout = _Stream([])
        _FakePopen.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def wait(self):
        pass


class _FakeHelper:
    orientation = 6

    def __init__(self, *args, **kwargs):
        self.set_calls = []

    def get_tags(self, fullname, tag):
        if _FakeHelper.orientation is None:
            return [{}]
        return [{rotator.ORIENTATION_TAG: _FakeHelper.orientation}]

    def set_tags(self, fullname, tags):
        self.set_calls.append((fullname, tags))

    def terminate(self):
        pass


@pytest.fixture(autouse=True)
def _reset():
    _FakePopen.instances = []
    _FakePopen.stderr_lines = []
    _FakeHelper.orientation = 6
    yield


# --- exiftran path ---


def test_exiftran_argv_and_success(cfg, monkeypatch):
    cfg.set('main', 'use_jpegtran', '0')
    _FakePopen.stderr_lines = ['processing img.jpg\n']
    monkeypatch.setattr(rotator.subprocess, 'Popen', _FakePopen)

    r = rotator.Rotator(cfg, ['/x/img.jpg'], dryrun=False)
    r.run()

    assert _FakePopen.instances[0].args == ['exiftran', '-aip', '/x/img.jpg']
    assert r.status()['good'] == 1
    assert r.status()['errors'] == 0


def test_exiftran_error_counted(cfg, monkeypatch):
    cfg.set('main', 'use_jpegtran', '0')
    _FakePopen.stderr_lines = ['some failure\n']
    monkeypatch.setattr(rotator.subprocess, 'Popen', _FakePopen)

    r = rotator.Rotator(cfg, ['/x/img.jpg'], dryrun=False)
    r.run()

    assert r.status()['errors'] == 1
    assert r.status()['good'] == 0


def test_exiftran_dryrun_skips_subprocess(cfg, monkeypatch):
    cfg.set('main', 'use_jpegtran', '0')
    monkeypatch.setattr(rotator.subprocess, 'Popen', _FakePopen)

    r = rotator.Rotator(cfg, ['/x/img.jpg'], dryrun=True)
    r.run()

    assert not _FakePopen.instances
    assert r.status()['good'] == 1


# --- jpegtran path ---


@pytest.fixture
def jpeg_cfg(cfg, monkeypatch):
    cfg.set('main', 'use_jpegtran', '1')
    monkeypatch.setattr(rotator.exiftool, 'ExifToolHelper', _FakeHelper)
    monkeypatch.setattr(rotator.subprocess, 'Popen', _FakePopen)
    return cfg


def test_jpegtran_builds_list_argv(tmp_path, jpeg_cfg):
    img = tmp_path / 'img.jpg'
    img.write_bytes(b'x')
    _FakeHelper.orientation = 6

    r = rotator.Rotator(jpeg_cfg, [str(img)], dryrun=False)
    r.run()

    args = _FakePopen.instances[0].args
    assert isinstance(args, list)
    assert args[:4] == ['jpegtran', '-copy', 'all', '-outfile']
    assert args[5:] == ['-rotate', '90', str(img)]
    assert args[4].startswith(str(tmp_path))  # temp file lives beside the source
    assert img.exists()  # temp file renamed back into place
    assert r.status()['good'] == 1


@pytest.mark.parametrize(
    'orientation,expected',
    [
        (2, ['-flip', 'horizontal']),
        (3, ['-rotate', '180']),
        (4, ['-flip', 'vertical']),
        (5, ['-transpose']),
        (6, ['-rotate', '90']),
        (7, ['-transverse']),
        (8, ['-rotate', '270']),
    ],
)
def test_jpegtran_orientation_mapping(tmp_path, jpeg_cfg, orientation, expected):
    img = tmp_path / 'img.jpg'
    img.write_bytes(b'x')
    _FakeHelper.orientation = orientation

    rotator.Rotator(jpeg_cfg, [str(img)], dryrun=False).run()

    assert _FakePopen.instances[0].args[5:] == expected + [str(img)]


@pytest.mark.parametrize('orientation', [0, 1, None])
def test_jpegtran_noop_orientations(tmp_path, jpeg_cfg, orientation):
    img = tmp_path / 'img.jpg'
    img.write_bytes(b'x')
    _FakeHelper.orientation = orientation

    r = rotator.Rotator(jpeg_cfg, [str(img)], dryrun=False)
    r.run()

    assert not _FakePopen.instances
    assert r.status()['good'] == 1
    assert img.read_bytes() == b'x'


def test_jpegtran_dryrun_skips_subprocess(tmp_path, jpeg_cfg):
    img = tmp_path / 'img.jpg'
    img.write_bytes(b'x')
    _FakeHelper.orientation = 6

    r = rotator.Rotator(jpeg_cfg, [str(img)], dryrun=True)
    r.run()

    assert not _FakePopen.instances
    assert r.status()['good'] == 1
    assert img.read_bytes() == b'x'


def test_jpegtran_failure_keeps_original(tmp_path, jpeg_cfg):
    img = tmp_path / 'img.jpg'
    img.write_bytes(b'x')
    _FakeHelper.orientation = 6
    _FakePopen.stderr_lines = ['jpegtran: bad file\n']

    r = rotator.Rotator(jpeg_cfg, [str(img)], dryrun=False)
    r.run()

    assert r.status()['errors'] == 1
    assert img.exists()
