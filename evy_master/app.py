# -*- coding: utf-8 -*-
import multiprocessing
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from gunicorn.app.base import Application

from evy_master.main import create_app

def counter_workers():
    return (multiprocessing.cpu_count() * 2) + 1

class MasterApp(Application):
    def __init__(self, options=None):
        if options is None:
            options = {}

        self.prog = None
        self.usage = None
        self.callable = None
        self.options = options
        self.do_load_config()

    def init(self, parser, opts, args):
        config = dict(
            (key, value)
            for key, value in map(lambda item: (item[0].lower(), item[1]),
                self.options.iteritems())
            if key in self.cfg.settings and value is not None
        )

        return config

    def load(self):
        app = create_app()
        app.wsgi_app = ProxyFix(app.wsgi_app)
        return app

def main():
    options = {
        'bind': '127.0.0.1:19000',
        'debug': True,
        'loglevel': 'debug',
        'pidfile': '/tmp/master.evy.pid',
        'proc_name': 'Evy Master',
        'workers': 1, #counter_workers(),
    }

    # Can be monitored by supervisord
    MasterApp(options).run()
