from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.5.4'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Jellyfin'
    ext_name = 'jellyfin'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['username'] = config.String()
        schema['user_id'] = config.String(optional=True)
        schema['password'] = config.Secret()
        schema['hostname'] = config.String()
        schema['libraries'] = config.String(optional=True)
        schema['port'] = config.Port()
        schema['client_cert'] = config.String(optional=True)
        schema['client_key'] = config.String(optional=True)

        return schema

    def setup(self, registry):
        from .backend import JellyfinBackend
        registry.add('backend', JellyfinBackend)
