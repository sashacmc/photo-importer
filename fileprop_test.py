#!/usr/bin/python3

import unittest
import config
import fileprop
import datetime


class TestFileProp(unittest.TestCase):
    def setUp(self):
        self.conf = config.Config()

    # photo
    def test_camera_photo(self):
        fp = fileprop.FileProp(self.conf, 'DSC_0846.JPG')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone1_photo(self):
        fp = fileprop.FileProp(self.conf, 'IMG_20180413_173249204.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 4, 13, 17, 32, 49))
        self.assertEqual(fp.ok(), False)

    def test_phone2_photo(self):
        fp = fileprop.FileProp(self.conf, '2018-02-26-18-30-36-816.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), False)

    def test_phone3_photo(self):
        fp = fileprop.FileProp(self.conf, '20180306124843.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 3, 6, 12, 48, 43))
        self.assertEqual(fp.ok(), False)

    def test_phone4_photo(self):
        fp = fileprop.FileProp(self.conf, 'P_20170818_191317_1.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 8, 18, 19, 13, 17))
        self.assertEqual(fp.ok(), False)

    def test_phone5_photo(self):
        fp = fileprop.FileProp(self.conf, 'P_20171010_083339_BF.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 10, 10, 8, 33, 39))
        self.assertEqual(fp.ok(), False)

    def test_phone6_photo(self):
        fp = fileprop.FileProp(self.conf, 'zcamera-20171115_054429.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 15, 5, 44, 29))
        self.assertEqual(fp.ok(), False)

    def test_phone7_photo(self):
        fp = fileprop.FileProp(self.conf, 'IMG-20171205-WA0006.jpeg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2017, 12, 5))
        self.assertEqual(fp.ok(), False)

    def test_phone8_photo(self):
        fp = fileprop.FileProp(self.conf, 'DSC_0001_1523811900639.JPG')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone9_photo(self):
        fp = fileprop.FileProp(self.conf, 'DSC_0119a.JPG')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_valid1_photo(self):
        fp = fileprop.FileProp(self.conf, '2018-02-26_18-30-36.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), True)

    def test_valid2_photo(self):
        fp = fileprop.FileProp(self.conf, '2018-02-26_18-30-36_9.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), datetime.datetime(2018, 2, 26, 18, 30, 36))
        self.assertEqual(fp.ok(), True)

    # video
    def test_camera_video(self):
        fp = fileprop.FileProp(self.conf, 'MOV_1422.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_videoshow_video(self):
        fp = fileprop.FileProp(
            self.conf,
            'Video_20171107123943353_by_videoshow.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 7, 12, 39, 43))
        self.assertEqual(fp.ok(), False)

    def test_phone1_video(self):
        fp = fileprop.FileProp(self.conf, 'VID-20180407-WA0000_0811.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2018, 4, 7))
        self.assertEqual(fp.ok(), False)

    def test_phone2_video(self):
        fp = fileprop.FileProp(self.conf, 'video_2017-12-28T22.13.03.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 12, 28, 22, 13, 3))
        self.assertEqual(fp.ok(), False)

    # audio
    def test_phone1_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20170924-WA0002.3gpp')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 9, 24))
        self.assertEqual(fp.ok(), False)

    def test_phone2_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20170924-WA0001.mp3')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 9, 24))
        self.assertEqual(fp.ok(), False)

    def test_phone3_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20171122-WA0000.m4a')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), datetime.datetime(2017, 11, 22))
        self.assertEqual(fp.ok(), False)

    # garbage
    def test_garbage(self):
        fp = fileprop.FileProp(self.conf, 'M0101.CTG')
        self.assertEqual(fp.type(), fp.GARBAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)


if __name__ == '__main__':
    unittest.main()
