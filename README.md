# Photo Importer

![CodeQL](https://github.com/sashacmc/photo-importer/workflows/CodeQL/badge.svg)
![Codespell](https://github.com/sashacmc/photo-importer/actions/workflows/codespell.yml/badge.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/photo-importer.svg)](https://pypi.org/project/photo-importer)
[![PyPI - Downloads](https://pepy.tech/badge/photo-importer)](https://pepy.tech/project/photo-importer)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A command-line tool and standalone web server for importing, renaming, and rotating photos and videos from cameras, USB drives, and memory cards.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Acknowledgements](#acknowledgements)

---

## Features

### photo-importer (CLI)

- Scans directories for media files (images, video, audio)
- Detects capture time via EXIF metadata, filename patterns, or file attributes
- Organises files into a configurable date-based directory hierarchy
- Renames files according to capture timestamp
- Performs lossless JPEG rotation (via [exiftran](https://linux.die.net/man/1/exiftran) or [jpegtran](https://linux.die.net/man/1/jpegtran))
- Supports dry-run mode for previewing changes without modifying files

### photo-importer-server (Web UI)

- Standalone web server for use on headless machines (e.g. a home server or Raspberry Pi)
- Detects mounted removable storage by path mask
- Provides one-click mount, import, and unmount via a browser interface
- Same import pipeline as the CLI tool

---

## Installation

### Requirements

- Python 3.6+

### Supported Platforms

| Platform | Support |
|---|---|
| Debian-based Linux | Full (CLI + Web) |
| Other Linux | Unofficial (likely works) |
| Windows 7+ | CLI + Web |
| macOS (with Homebrew) | CLI only |

### System Dependencies

| Dependency | Purpose |
|---|---|
| [exiftool](https://exiftool.org/) | EXIF metadata reading |
| [exiftran](https://linux.die.net/man/1/exiftran) or [jpegtran](https://linux.die.net/man/1/jpegtran) | Lossless JPEG rotation |
| [pmount](https://linux.die.net/man/1/pmount) | Storage mount/unmount (server only) |

### Python Dependencies

- [PyExifTool](https://pypi.org/project/PyExifTool/)
- [progressbar](https://pypi.org/project/progressbar/)
- [psutil](https://pypi.org/project/psutil/)
- [pypiwin32](https://pypi.org/project/pypiwin32/) *(Windows only)*

### Installing via PyPI *(recommended)*

```bash
sudo apt install exiftran exiftool pmount pip
sudo pip install photo-importer
```

### Installing as a Debian Package

```bash
debuild -b
sudo apt install pip python3-exif python3-progressbar exiftran python3-psutil
sudo pip install PyExifTool
sudo dpkg -i ../photo-importer_*.deb
```

### Installing from Source

```bash
sudo apt install exiftran exiftool pmount pip
sudo pip install PyExifTool progressbar psutil
sudo python3 ./setup.py install
```

### Installing on Windows

1. Download and install [Python 3](https://www.python.org/downloads/windows/)
2. Download and install [ExifTool](https://exiftool.org/)
3. Download and extract [jpegtran](http://sylvana.net/jpegcrop/jpegtran/) into the `photo_importer` folder
4. Install the package and its Windows dependencies:

```bat
python -m pip install pypiwin32 photo-importer
```

---

## Usage

### Command-Line Interface

**In-place processing** — rename and rotate files without moving them:

```bash
photo-importer /path/to/media/files
```

![In place example](https://user-images.githubusercontent.com/28735879/76139947-bd249780-6055-11ea-85c0-0985b6bde93f.png)

**Import to output directory** — move (or copy) files into a date-based hierarchy:

```bash
photo-importer /path/to/media/files /output/path
```

Files are moved by default. To copy instead, set `move_mode = 0` in the config file.

![Move example](https://user-images.githubusercontent.com/28735879/76139964-eba27280-6055-11ea-988f-aa71cda7ba36.png)

**CLI options:**

| Option | Description |
|---|---|
| `in_path` | Source directory to scan (required) |
| `out_path` | Destination directory (optional; in-place mode if omitted) |
| `-c`, `--config FILE` | Path to a custom config file |
| `-l`, `--logfile FILE` | Log file path (default: `log.txt`) |
| `-d`, `--dryrun` | Dry run — preview actions without modifying files |

### Web Interface

1. Attach a USB drive or insert a memory card
2. Open `http://<hostname>:8080` in a browser
3. Click **Mount**
4. Click **Import**
5. Click **Unmount**

![Web interface example](https://user-images.githubusercontent.com/28735879/76140174-f1995300-6057-11ea-8718-19c38650c786.png)

### Windows — Command Line

```bat
cd photo_importer
python run.py -c ..\photo-importer-win.cfg path\to\media\files \output\path
```

### Windows — Web Server

```bat
photo-importer-server.bat
```

---

## Configuration

| Scope | Default config file |
|---|---|
| CLI tool | `~/.photo-importer.cfg` |
| Web server | `/etc/photo-importer.cfg` |

A custom config file can be passed to the CLI with the `-c` option.

All available options are documented with comments inside the config file itself.

---

## Acknowledgements

Thanks to everyone who tested the tool and provided feedback.

Bug reports, suggestions, and pull requests are welcome!

## Show Your Support

Give a ⭐️ if this project helped you!
