# pylint: disable=unused-argument,too-few-public-methods

import pytest

from photo_importer import config
from photo_importer import fileprop


@pytest.fixture
def cfg():
    """A Config built only from defaults — never reads host config files."""
    return config.Config(use_system_config=False)


class _FakeExifTool:
    """Minimal stand-in for exiftool.ExifToolHelper.

    Returns no metadata/tags so callers fall back to name/attr based timing,
    and never spawns the real exiftool process.
    """

    def __init__(self, *args, **kwargs):
        pass

    def get_metadata(self, *args, **kwargs):
        return [{}]

    def get_tags(self, *args, **kwargs):
        return [{}]

    def set_tags(self, *args, **kwargs):
        pass

    def terminate(self):
        pass


@pytest.fixture
def fake_exiftool(monkeypatch):
    """Replace ExifToolHelper everywhere so tests don't need the binary."""
    monkeypatch.setattr(fileprop.exiftool, 'ExifToolHelper', _FakeExifTool)
    return _FakeExifTool
