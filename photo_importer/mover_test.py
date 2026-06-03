#!/usr/bin/python3
# pylint: disable=redefined-outer-name,unused-argument,too-few-public-methods

import os

import pytest

from photo_importer import mover


def _file(tmp_path, name='2021-12-19_13-11-36.jpg', data=b'data'):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


@pytest.fixture
def cfg_name(cfg):
    cfg.set('main', 'time_src_image', 'name')
    cfg.set('main', 'time_src_video', 'name')
    cfg.set('main', 'time_src_audio', 'name')
    return cfg


def _dst(out):
    return out / 'Foto' / '2021' / '2021-12-19' / '2021-12-19_13-11-36.jpg'


# --- dryrun (regression: use_shutil used to bypass the dryrun guard) ---


def test_dryrun_with_shutil_does_not_touch_files(tmp_path, cfg_name, fake_exiftool, monkeypatch):
    src = _file(tmp_path)
    cfg_name.set('main', 'use_shutil', '1')
    cfg_name.set('main', 'move_mode', '1')
    calls = []
    monkeypatch.setattr(mover.shutil, 'move', lambda s, d: calls.append((s, d)))
    monkeypatch.setattr(mover.shutil, 'copy2', lambda s, d: calls.append((s, d)))

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [src], dryrun=True)
    res = m.run()

    assert not calls
    assert os.path.exists(src)
    assert m.status()['moved'] == 1
    assert len(res) == 1


# --- copy / move via shutil ---


def test_copy_creates_file_and_keeps_source(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path)
    cfg_name.set('main', 'use_shutil', '1')
    cfg_name.set('main', 'move_mode', '0')
    out = tmp_path / 'out'

    mover.Mover(cfg_name, str(out), [src], dryrun=False).run()

    assert _dst(out).exists()
    assert os.path.exists(src)


def test_move_removes_source(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path)
    cfg_name.set('main', 'use_shutil', '1')
    cfg_name.set('main', 'move_mode', '1')
    out = tmp_path / 'out'

    m = mover.Mover(cfg_name, str(out), [src], dryrun=False)
    m.run()

    assert _dst(out).exists()
    assert not os.path.exists(src)
    assert m.status()['moved'] == 1


# --- copy / move via subprocess (cp / mv) ---


def test_subprocess_copy_with_cp(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path)
    cfg_name.set('main', 'use_shutil', '0')
    cfg_name.set('main', 'move_mode', '0')
    out = tmp_path / 'out'

    m = mover.Mover(cfg_name, str(out), [src], dryrun=False)
    m.run()

    assert _dst(out).exists()
    assert m.status()['copied'] == 1


# --- garbage ---


def test_garbage_removed(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, 'M0101.ctg')
    cfg_name.set('main', 'remove_garbage', '1')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [src], dryrun=False)
    m.run()

    assert not os.path.exists(src)
    assert m.status()['removed'] == 1


def test_garbage_skipped_when_disabled(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, 'M0101.ctg')
    cfg_name.set('main', 'remove_garbage', '0')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [src], dryrun=False)
    m.run()

    assert os.path.exists(src)
    assert m.status()['skipped'] == 1


# --- skip cases ---


def test_ignored_extension_skipped(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, 'archive.zip')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [src], dryrun=False)
    m.run()

    assert m.status()['skipped'] == 1


def test_no_detectable_time_skipped(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, 'DSC_0846.jpg')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [src], dryrun=False)
    m.run()

    assert m.status()['skipped'] == 1


# --- rename mode (no output path) ---


def test_rename_mode_without_output_path(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, 'IMG_20180413_173249204.jpg')

    m = mover.Mover(cfg_name, '', [src], dryrun=False)
    m.run()

    assert (tmp_path / '2018-04-13_17-32-49.jpg').exists()
    assert m.status()['moved'] == 1


def test_already_named_file_skipped(tmp_path, cfg_name, fake_exiftool):
    src = _file(tmp_path, '2018-04-13_17-32-49.jpg')

    m = mover.Mover(cfg_name, '', [src], dryrun=False)
    m.run()

    assert m.status()['skipped'] == 1


# --- error handling ---


def test_missing_source_counts_error(tmp_path, cfg_name, fake_exiftool):
    missing = str(tmp_path / '2021-12-19_13-11-36.jpg')  # never created
    cfg_name.set('main', 'use_shutil', '1')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [missing], dryrun=False)
    m.run()

    assert m.status()['errors'] == 1


def test_mv_failure_counts_error(tmp_path, cfg_name, fake_exiftool):
    missing = str(tmp_path / '2021-12-19_13-11-36.jpg')
    cfg_name.set('main', 'use_shutil', '0')
    cfg_name.set('main', 'move_mode', '1')

    m = mover.Mover(cfg_name, str(tmp_path / 'out'), [missing], dryrun=False)
    m.run()

    assert m.status()['errors'] == 1
