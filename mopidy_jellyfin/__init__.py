from __future__ import unicode_literals

import logging
import os
import socket

from mopidy import config, ext


__version__ = '0.9.1'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Jellyfin'
    ext_name = 'jellyfin'
    version = __version__
    device_name = socket.gethostname()
    device_id = dist_name + '-' + socket.gethostname()

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['username'] = config.String()
        schema['user_id'] = config.String(optional=True)
        schema['password'] = config.Secret(optional=True)
        schema['hostname'] = config.String()
        schema['libraries'] = config.String(optional=True)
        schema['albumartistsort'] = config.String(optional=True)
        schema['port'] = config.Port(optional=True)
        schema['client_cert'] = config.String(optional=True)
        schema['client_key'] = config.String(optional=True)
        schema['album_format'] = config.String(optional=True)
        schema['max_bitrate'] = config.Integer(optional=True)

        return schema

    def setup(self, registry):
        from .backend import JellyfinBackend
        from .frontend import EventMonitorFrontend
        registry.add('backend', JellyfinBackend)
        registry.add('frontend', EventMonitorFrontend)
