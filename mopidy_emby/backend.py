from __future__ import unicode_literals

import logging
import pykka

from mopidy import backend

from .library import EmbyLibraryProvider
from .emby import EmbyHandler


logger = logging.getLogger(__name__)


class EmbyBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['emby']

    def __init__(self, config, audio):
        super(EmbyBackend, self).__init__()

        self.library = EmbyLibraryProvider(backend=self)
        self.playback = None
        self.playlist = None
        self.remote = EmbyHandler()
