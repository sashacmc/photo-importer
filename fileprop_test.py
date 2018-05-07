#!/usr/bin/python3

import unittest
import config
import fileprop


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
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone2_photo(self):
        fp = fileprop.FileProp(self.conf, '2018-02-26-18-30-36-816.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone3_photo(self):
        fp = fileprop.FileProp(self.conf, '20180306124843.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone4_photo(self):
        fp = fileprop.FileProp(self.conf, 'P_20170818_191317_1.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone5_photo(self):
        fp = fileprop.FileProp(self.conf, 'P_20171010_083339_BF.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone6_photo(self):
        fp = fileprop.FileProp(self.conf, 'zcamera-20171115_054429.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone_photo(self):
        fp = fileprop.FileProp(self.conf, 'IMG-20171205-WA0006.jpeg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone_photo(self):
        fp = fileprop.FileProp(self.conf, '2017-11-16-01-23-37-377.jpg')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone_photo(self):
        fp = fileprop.FileProp(self.conf, 'DSC_0001_1523811900639.JPG')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone_photo(self):
        fp = fileprop.FileProp(self.conf, 'DSC_0119a.JPG')
        self.assertEqual(fp.type(), fp.IMAGE)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

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
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone1_video(self):
        fp = fileprop.FileProp(self.conf, 'VID-20180407-WA0000_0811.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone2_video(self):
        fp = fileprop.FileProp(self.conf, 'video_2017-12-28T22.13.33.mp4')
        self.assertEqual(fp.type(), fp.VIDEO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    # audio
    def test_phone1_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20170924-WA0002.3gpp')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone2_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20170924-WA0001.mp3')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)

    def test_phone3_audio(self):
        fp = fileprop.FileProp(self.conf, 'AUD-20171122-WA0000.m4a')
        self.assertEqual(fp.type(), fp.AUDIO)
        self.assertEqual(fp.time(), None)
        self.assertEqual(fp.ok(), False)


if __name__ == '__main__':
    unittest.main()
