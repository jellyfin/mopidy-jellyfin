from __future__ import unicode_literals

import logging

from mopidy import backend, models


logger = logging.getLogger(__name__)


class EmbyLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='emby:library',
                                          name='Emby library')

    def browse(self, uri):
        if uri == root_directory.uri:
            return []
