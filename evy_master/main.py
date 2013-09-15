# -*- coding: utf-8 -*-
import uuid
import functools

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for

from flask.ext.restful import Api
from flask.ext.restful import Resource
from flask.ext.rq import get_queue

import requests
import redis

from evy_master.extensions import bootstrap
from evy_master.extensions import rq
from evy_master.extensions import cache
from evy_master.config import DefaultConfig

from flask.ext.restful import reqparse


class BuildsResource(Resource):
    def post(self):
        # Will create a new build, receive the branch
        # args = parser.parse_args()
        parser = reqparse.RequestParser()
        parser.add_argument('branch', type=str)

        print parser.parse_args()

        branch = False
        if request.json:
            if 'branch' in request.json:
                branch = request.json['branch']
        else:
            return (
                {'error': 'The branch parameter is not present in the request'},
                requests.codes.bad_request,
            )

        identifier = uuid.uuid4().hex

        values = {
            'identifier': identifier,
            'branch': branch,
        }

        plugin_name = 'email'
        document = {
            'from': 'Stephane Wirtel <stephane@wirtel.be>',
        }
        to_plugin = functools.partial(
            get_queue('builds').enqueue,
            'evy_worker.extension.invoke_plugin'
        )

        to_plugin(plugin_name, document)

        #get_queue('builds').enqueue('evy_worker.extension.plugin',
        #        'email', {'from': 'Stephane Wirtel <stephane@wirtel.be>',
        #            })

        #get_queue('builds').enqueue('evy_worker.build.create',
        #                            branch,
        #                            identifier)

        headers = {
            'Location': url_for(BuildResource.__name__.lower(),
                                _method='GET', identifier=identifier),
            'X-Evy-Build': identifier,
        }

        return ({}, requests.codes.accepted, headers)

class BuildResource(Resource):
    def get(self, identifier):
        key = "builds:%s" % (identifier,)
        conn = redis.Redis('localhost', 6379)
        build = conn.hgetall(key)
        build.update({'identifier': identifier})
        return build

    def delete(self, identifier):
        return {}

def configure_api(app):
    api = Api(app, '/api/v1')
    api.add_resource(BuildsResource, '/builds')
    api.add_resource(BuildResource, '/builds/<identifier>')
    return api

class App(Flask):
    def __init__(self, *args, **kwargs):
        config = kwargs.pop('config', None)
        Flask.__init__(self, *args, **kwargs)

        self.config.from_object(DefaultConfig())

        if config is not None:
            if isinstance(config, basestring):
                self.config.from_pyfile(config)
            else:
                self.config.from_object(config)

        self.configure_extensions()

    def configure_extensions(self):
        bootstrap.init_app(self)
        rq.init_app(self)
        cache.init_app(self)
        self.api = configure_api(self)

def create_app(config=None):
    app = App(__name__, config=config)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app



