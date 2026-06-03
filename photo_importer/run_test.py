#!/usr/bin/python3
# pylint: disable=redefined-outer-name,unused-argument,too-few-public-methods

import sys

from photo_importer import run


def test_args_parse_full(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog', '/in', '/out', '-d', '-c', 'cfg.ini'])
    args = run.args_parse()
    assert args.in_path == '/in'
    assert args.out_path == '/out'
    assert args.dryrun is True
    assert args.config == 'cfg.ini'


def test_args_parse_optional_outpath(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog', '/in'])
    args = run.args_parse()
    assert args.in_path == '/in'
    assert args.out_path is None
    assert args.dryrun is False


class _FakeImporter:
    def __init__(self, statuses):
        self._statuses = list(statuses)
        self._last = self._statuses[-1]

    def status(self):
        if self._statuses:
            return self._statuses.pop(0)
        return self._last


def test_progressbar_runs_through_stages(capsys):
    statuses = [
        {'stage': 'scan'},
        {'stage': 'move', 'total': 2},
        {'stage': 'move', 'total': 2, 'move': {'processed': 1}},
        {'stage': 'rotate', 'total': 2},
        {'stage': 'rotate', 'total': 2, 'rotate': {'processed': 2}},
        {'stage': 'done'},
    ]
    run.ProgressBar(_FakeImporter(statuses)).run()
    assert 'Found 2 files' in capsys.readouterr().out


def test_main_on_empty_dir(tmp_path, monkeypatch, fake_exiftool):
    indir = tmp_path / 'in'
    indir.mkdir()
    cfgfile = tmp_path / 'c.cfg'
    cfgfile.write_text('[main]\nuse_jpegtran = 0\n')
    logfile = tmp_path / 'log.txt'
    monkeypatch.setattr(
        sys,
        'argv',
        ['prog', str(indir), str(tmp_path / 'out'), '-c', str(cfgfile), '-l', str(logfile)],
    )

    run.main()

    assert logfile.exists()
