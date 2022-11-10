from setuptools import setup
setup(name='photo-importer',
      version='1.1.1',
      description='Photo importer tool',
      author='Alexander Bushnev',
      author_email='Alexander@Bushnev.pro',
      license='GNU General Public License v3.0',
      packages=['photo_importer'],
      data_files=[('/etc/',
                   ['photo-importer.cfg']),
                  ('/lib/systemd/system/',
                   ['photo-importer.service']),
                  ('share/photo-importer/web/',
                   ['web/index.html', 'web/log.png'])],
      install_requires=['PyExifTool', 'progressbar', 'psutil'],
      scripts=['photo-importer', 'photo-importer-server'],
      zip_safe=False)
