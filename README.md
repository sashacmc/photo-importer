# Photo Importer

[![Total alerts](https://img.shields.io/lgtm/alerts/g/sashacmc/photo-importer.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/sashacmc/photo-importer/alerts/)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/sashacmc/photo-importer.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/sashacmc/photo-importer/context:javascript)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/sashacmc/photo-importer.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/sashacmc/photo-importer/context:python)

Command line tools for photo importing/renaming/rotating
### Features:
  * Media files scan
  * Time when picture was taken detection (by EXIF, by file name, by file attributes)
  * Media files moving/copying to configurable hierarchy 
  * Lossless rotations (via exiftran or jpegtran)

# Photo Importer Server
Standalone web server for fast media import for headless computer
### Features:
  * Mounted storages detection (by path mask)
  * Storages mount/unmount (via pmount)
  * The same as photo-importer but without console

# Installation

### Requirements:

  * Python 3.3+

### Supported OS:

  * Debian based Linux (other Linux versions not officially supported, but might work)
  * Windows 7 and above
  * MacOS X and above (with brew installed, only console version)

### Dependencies:
  * [PyExifTool](https://pypi.org/project/PyExifTool/)
  * [progressbar](https://pypi.org/project/progressbar/)
  * [psutil](https://pypi.org/project/psutil/)
  * [exiftran](https://linux.die.net/man/1/exiftran) or [jpegtran](https://linux.die.net/man/1/jpegtran)
  * [pmount](https://linux.die.net/man/1/pmount) (only for server)
  * [pypiwin32](https://pypi.org/project/pypiwin32/) (only for windows)


### Installation Options:

#### Installing via PyPi
```bash
sudo apt install exiftran exiftool pmount pip
sudo pip install photo-importer
```
#### Installing as debian package
```bash
debuild -b
sudo dpkg -i ../photo-importer_1.2.0_all.deb
```
#### Installing via setup.py
```bash
sudo apt install exiftran exiftool pmount pip
sudo pip install PyExifTool progressbar psutil
sudo python3 ./setup.py install
```

#### Installing for Windows
Download and install python3 for you Windows distributive
https://www.python.org/downloads/windows/

Download and install exiftool
https://exiftool.org/

Download and extract jpegtran to photo_importer folder
http://sylvana.net/jpegcrop/jpegtran/

Install with python dependencies
```bash
python -m pip install pypiwin32 photo-importer
```

## Usage
### Command-Line Interface

```bash
photo-importer /path/to/media/files
```
Will process files (reanaming/rotating) in-place.
![In place example](https://user-images.githubusercontent.com/28735879/76139947-bd249780-6055-11ea-85c0-0985b6bde93f.png)

```bash
photo-importer /path/to/media/files /output/path
```
Will import (by default move, but it can be changed in config) files from /path/to/media/files to /output/path with date hierarchy creation and reanaming/rotating

![Move example](https://user-images.githubusercontent.com/28735879/76139964-eba27280-6055-11ea-988f-aa71cda7ba36.png)

### Web Interface
  * attach usb-drive / usert memory card
  * open http://servername:8080
  * click "Mount"
  * click "Import"
  * click "Unmount"

![Web interface example](https://user-images.githubusercontent.com/28735879/76140174-f1995300-6057-11ea-8718-19c38650c786.png)

### Windows command line
```bash
cd photo_importer
run.py -c ..\photo-importer-win.cfg path\to\media\files \output\path
```
### Windows web 
```bash
photo-importer-server.bat
```

## Configuration
The server config file located in /etc/photo-importer.cfg

Command line tool config file located in ~/.photo-importer.cfg

Also config file can be specified by mean of -c command line option.

For options details see comments in the config file.

## Acknowledgements
Thanks to everyone who tested and gave advice.

**Bug reports, suggestions and pull request are welcome!**
