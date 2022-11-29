#!/usr/bin/python3

import os
import unittest
import tempfile

from . import config
from . import importer


class TestImporter(unittest.TestCase):
    def test_importer(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            cfg = config.Config()
            cfg.set('main', 'move_mode', '0')
            imp = importer.Importer(
                cfg,
                os.path.join(os.path.dirname(__file__), 'test_data'),
                tmpdirname,
                False,
            )
            imp.start()
            imp.join()

            self.assertEqual(
                imp.status(),
                {
                    'stage': 'done',
                    'total': 2,
                    'move': {
                        'total': 2,
                        'moved': 0,
                        'copied': 2,
                        'removed': 0,
                        'skipped': 0,
                        'processed': 2,
                        'errors': 0,
                    },
                    'rotate': {
                        'total': 2,
                        'processed': 2,
                        'good': 2,
                        'errors': 0,
                    },
                },
            )

            files = []
            for path, cd, fs in os.walk(tmpdirname):
                for f in fs:
                    print(os.path.join(path, f))
                    files.append(os.path.join(path, f))
            files.sort()

            self.assertEqual(len(files), 2)
            self.assertEqual(
                files[0],
                os.path.join(
                    tmpdirname, 'Foto/2021/2021-12-19/2021-12-19_13-11-36.jpeg'
                ),
            )
            self.assertEqual(
                files[1],
                os.path.join(
                    tmpdirname, 'Foto/2022/2022-11-21/2022-11-21_00-42-07.JPG'
                ),
            )
