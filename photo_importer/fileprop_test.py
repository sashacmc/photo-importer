#!/usr/bin/python3

import unittest
import datetime

from . import config
from . import fileprop


class TestFileProp(unittest.TestCase):
    def setUp(self):
        self.conf = config.Config()
        self.fp = fileprop.FileProp(self.conf)
        self.conf.set('main', 'time_src_image', 'name')
        self.conf.set('main', 'time_src_video', 'name')
        self.conf.set('main', 'time_src_audio', 'name')

    # photo
    def test_camera_photo(self):
        fp = self.fp.get('DSC_0846.JPG')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone1_photo(self):
        fp = self.fp.get('IMG_20180413_173249204.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 4, 13, 17, 32, 49))
        self.assertEqual(fp.ok(), False)

    def test_phone2_photo(self):
        fp = self.fp.get('2018-02-26-18-30-36-816.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), False)

    def test_phone3_photo(self):
        fp = self.fp.get('20180306124843.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 3, 6, 12, 48, 43))
        self.assertEqual(fp.ok(), False)

    def test_phone4_photo(self):
        fp = self.fp.get('P_20170818_191317_1.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 8, 18, 19, 13, 17))
        self.assertEqual(fp.ok(), False)

    def test_phone5_photo(self):
        fp = self.fp.get('P_20171010_083339_BF.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 10, 10, 8, 33, 39))
        self.assertEqual(fp.ok(), False)

    def test_phone6_photo(self):
        fp = self.fp.get('zcamera-20171115_054429.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 15, 5, 44, 29))
        self.assertEqual(fp.ok(), False)

    def test_phone7_photo(self):
        fp = self.fp.get('IMG-20171205-WA0006.jpeg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 12, 5))
        self.assertEqual(fp.ok(), False)

    def test_phone8_photo(self):
        fp = self.fp.get('DSC_0001_1523811900639.JPG')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone9_photo(self):
        fp = self.fp.get('DSC_0119a.JPG')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_valid1_photo(self):
        fp = self.fp.get('2018-02-26_18-30-36.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), True)

    def test_valid2_photo(self):
        fp = self.fp.get('2018-02-26_18-30-36_9.jpg')
        self.assertEqual(fp.type(), fileprop.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), True)

    # video
    def test_camera_video(self):
        fp = self.fp.get('MOV_1422.mp4')
        self.assertEqual(fp.type(), fileprop.VIDEO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_videoshow_video(self):
        fp = self.fp.get('Video_20171107123943353_by_videoshow.mp4')
        self.assertEqual(fp.type(), fileprop.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 7, 12, 39, 43))
        self.assertEqual(fp.ok(), False)

    def test_phone1_video(self):
        fp = self.fp.get('VID-20180407-WA0000_0811.mp4')
        self.assertEqual(fp.type(), fileprop.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2018, 4, 7))
        self.assertEqual(fp.ok(), False)

    def test_phone2_video(self):
        fp = self.fp.get('video_2017-12-28T22.13.03.mp4')
        self.assertEqual(fp.type(), fileprop.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 12, 28, 22, 13, 3))
        self.assertEqual(fp.ok(), False)

    # audio
    def test_phone1_audio(self):
        fp = self.fp.get('AUD-20170924-WA0002.3gpp')
        self.assertEqual(fp.type(), fileprop.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 9, 24))
        self.assertEqual(fp.ok(), False)

    def test_phone2_audio(self):
        fp = self.fp.get('AUD-20170924-WA0001.mp3')
        self.assertEqual(fp.type(), fileprop.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 9, 24))
        self.assertEqual(fp.ok(), False)

    def test_phone3_audio(self):
        fp = self.fp.get('AUD-20171122-WA0000.m4a')
        self.assertEqual(fp.type(), fileprop.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 22))
        self.assertEqual(fp.ok(), False)

    def test_phone4_audio(self):
        fp = self.fp.get('2020_05_12_15_07_20.mp3')
        self.assertEqual(fp.type(), fileprop.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2020, 5, 12, 15, 7, 20))
        self.assertEqual(fp.ok(), False)

    # garbage
    def test_garbage(self):
        fp = self.fp.get('M0101.CTG')
        self.assertEqual(fp.type(), fileprop.GARBAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)
