# photo-importer
Command line tools for photo importing/renaming/rotating
### Features:
  * Media files scan
  * Time when picture was taken detection (by EXIF, by file name, by file attributes)
  * Media files moving/copying to configurable hierarchy 
  * Lossless rotations (via exiftran)

# photo-importer-server
Standalone web server for fast media import for headless computer
### Features:
  * Mounted storages detection (by path mask)
  * Storages mount/unmount (via pmount)
  * The same as photo-importer but without console

## Installation

### Requirements:

  * Python 3.3+
  * Debian based Linux (Other Linux versions not officially supported, but might work)

### Dependencies:
  * python3-exif
  * python3-progressbar
  * python3-psutil
  * exiftran
  * pmount


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
