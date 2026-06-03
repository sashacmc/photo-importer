#!/usr/bin/python3
# pylint: disable=redefined-outer-name,unused-argument,too-few-public-methods

import os
import datetime

import pytest

from photo_importer import fileprop


class _Helper:
    """ExifToolHelper stand-in returning a configurable metadata dict."""

    metadata = {}

    def __init__(self, *args, **kwargs):
        pass

    def get_metadata(self, fullname):
        return [dict(_Helper.metadata)]

    def get_tags(self, *args, **kwargs):
        return [{}]

    def terminate(self):
        pass


@pytest.fixture
def exif_cfg(cfg, monkeypatch):
    monkeypatch.setattr(fileprop.exiftool, 'ExifToolHelper', _Helper)
    _Helper.metadata = {}
    return cfg


def test_time_by_exif(exif_cfg):
    _Helper.metadata = {'EXIF:DateTimeOriginal': '2020:05:01 12:00:00'}
    fp = fileprop.FileProp(exif_cfg).get('/x/photo.jpg')
    assert fp.type() == fileprop.IMAGE
    assert fp.time() == datetime.datetime(2020, 5, 1, 12, 0, 0)


def test_time_by_exif_strips_timezone(exif_cfg):
    _Helper.metadata = {'EXIF:CreateDate': '2020:05:01 12:00:00+03:00'}
    fp = fileprop.FileProp(exif_cfg).get('/x/photo.jpg')
    assert fp.time() == datetime.datetime(2020, 5, 1, 12, 0, 0)


def test_time_shift_applied(exif_cfg):
    _Helper.metadata = {'EXIF:DateTimeOriginal': '2020:05:01 12:00:00'}
    exif_cfg.set('main', 'time_shift', '3600')
    fp = fileprop.FileProp(exif_cfg).get('/x/photo.jpg')
    assert fp.time() == datetime.datetime(2020, 5, 1, 13, 0, 0)


def test_add_orig_name(exif_cfg):
    _Helper.metadata = {'EXIF:DateTimeOriginal': '2020:05:01 12:00:00'}
    exif_cfg.set('main', 'add_orig_name', '1')
    fp = fileprop.FileProp(exif_cfg).get('/x/holiday pic.jpg')
    assert fp.out_name() == '2020-05-01_12-00-00_holiday_pic'


def test_unknown_extension_is_ignored(exif_cfg):
    fp = fileprop.FileProp(exif_cfg).get('/x/file.xyz')
    assert fp.type() == fileprop.IGNORE
    assert fp.time() is None


def test_time_by_attr(tmp_path, exif_cfg):
    f = tmp_path / 'noexif.jpg'
    f.write_bytes(b'x')
    os.utime(f, (1590969600, 1590969600))  # 2020-06-01 UTC
    exif_cfg.set('main', 'time_src_image', 'attr')
    fp = fileprop.FileProp(exif_cfg).get(str(f))
    assert fp.time().year == 2020


def test_wrong_time_src_raises(exif_cfg):
    exif_cfg.set('main', 'time_src_image', 'bogus')
    with pytest.raises(UserWarning):
        fileprop.FileProp(exif_cfg).get('/x/photo.jpg')


def test_out_name_full_deduplicates(tmp_path, exif_cfg):
    exif_cfg.set('main', 'time_src_image', 'name')
    fp = fileprop.FileProp(exif_cfg)
    res = fp.get('2020-01-01_00-00-00.jpg')

    n1 = res.out_name_full(str(tmp_path))
    n2 = res.out_name_full(str(tmp_path))

    assert n1.endswith('2020-01-01_00-00-00.jpg')
    assert n2.endswith('2020-01-01_00-00-00_2.jpg')


def test_close_is_idempotent(exif_cfg):
    fp = fileprop.FileProp(exif_cfg)
    fp.close()
    fp.close()  # must not raise
