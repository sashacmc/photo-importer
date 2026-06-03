#!/usr/bin/python3

from photo_importer import config


def test_defaults_present():
    c = config.Config(use_system_config=False)
    assert c['main']['out_subdir_image'] == 'Foto'
    assert c['server']['port'] == '8080'


def test_use_system_config_flag(monkeypatch, tmp_path):
    sysfile = tmp_path / 'sys.cfg'
    sysfile.write_text('[main]\nout_subdir_image = FromSystem\n')
    monkeypatch.setattr(config.Config, 'DEFAULT_CONFIG_FILES', (str(sysfile),))

    assert config.Config(use_system_config=True)['main']['out_subdir_image'] == 'FromSystem'
    assert config.Config(use_system_config=False)['main']['out_subdir_image'] == 'Foto'


def test_explicit_file_overrides_defaults(tmp_path):
    cfgfile = tmp_path / 'c.cfg'
    cfgfile.write_text('[main]\nout_subdir_image = Pics\n')

    c = config.Config(str(cfgfile))

    assert c['main']['out_subdir_image'] == 'Pics'
    assert c['main']['out_subdir_video'] == 'Video'  # default preserved


def test_create_writes_file(tmp_path, monkeypatch):
    target = tmp_path / '.photo-importer.cfg'
    monkeypatch.setattr(config.Config, 'DEFAULT_CONFIG_FILES', (str(target), '/nonexistent'))

    config.Config(create=True, use_system_config=False)

    assert target.exists()


def test_set_updates_value():
    c = config.Config(use_system_config=False)
    c.set('main', 'move_mode', '0')
    assert c['main']['move_mode'] == '0'
