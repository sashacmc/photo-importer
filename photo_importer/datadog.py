from ddtrace import patch; patch(logging=True)

import os
import sys
import site
import pkg_resources
import logging
import ddtrace

sys.path.insert(0, os.path.abspath('..'))

from photo_importer import server # noqa

def calc_env():
    for p in site.getsitepackages():
        if p in __file__:
            return 'prod'
    return 'dev'

def apply_config():
    ddtrace.config.env = calc_env()
    ddtrace.config.service = 'photo-importer' 
    ddtrace.config.version = pkg_resources.require('photo-importer')[0].version 

def instrument_all(cls, excl):
    for attr in cls.__dict__:
        if callable(getattr(cls, attr)) and attr not in excl:
            setattr(cls, attr, ddtrace.tracer.wrap()(getattr(cls, attr)))

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')

def init_logger(filename):
    fh = logging.FileHandler(filename, 'a')
    fh.setFormatter(logging.Formatter(FORMAT))
    fh.setLevel(logging.INFO)
    logging.getLogger().addHandler(fh)

def enable():
    apply_config()
    instrument_all(server.PhotoImporterHandler, ('do_GET', 'do_POST'))
    init_logger('/var/log/user/photo-importer-server-datadog.log')

enable()



# DD_TAGS=git.repository_url:github.com/sashacmc/photo-importer git.commit.sha:2cc396adca87a55fbee63256ab7be188c432263f
