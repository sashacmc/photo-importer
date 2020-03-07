# photo-importer
Command line tools for photo importing/renaming/rotating

# photo-importer-server
Standalone web server for fast media import for headless computer

## Installation

### Requirements:

  * Python 3.3+
  * Debian based Linux (Other Linux versions not officially supported, but might work)

### Dependencies:
  * python3-exif
  * python3-progressbar
  * python3-psutil
  * exiftran


### Installation Options:

#### Installing as debian package
```bash
debuild -b
sudo dpkg -i ../photo-importer_1.0.1_all.deb
```
#### Installing via setup.py
```bash
sudo python3 ./setup.py install
```
