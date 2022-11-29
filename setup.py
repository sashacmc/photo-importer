from setuptools import setup
import os


def get_long_description():
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(
        os.path.join(this_directory, 'README.md'), encoding='utf-8'
    ) as f:
        long_description = f.read()

    return long_description


setup(
    name='photo-importer',
    version='1.2.0',
    description='Photo importer tool',
    author='Alexander Bushnev',
    author_email='Alexander@Bushnev.pro',
    license='GNU General Public License v3.0',
    packages=['photo_importer'],
    data_files=[
        ('/etc/', ['photo-importer.cfg']),
        ('/lib/systemd/system/', ['photo-importer.service']),
        ('share/photo-importer/web/', ['web/index.html', 'web/log.png']),
    ],
    install_requires=['PyExifTool', 'progressbar', 'psutil'],
    scripts=['photo-importer', 'photo-importer-server'],
    url='https://github.com/sashacmc/photo-importer',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Scientific/Engineering :: Image Processing',
        'Topic :: Multimedia :: Video',
        'Topic :: Utilities',
    ],
    zip_safe=False,
)
