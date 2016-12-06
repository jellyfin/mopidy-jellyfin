from __future__ import unicode_literals

import logging

from mopidy import backend

import pykka

from mopidy_emby.library import EmbyLibraryProvider
from mopidy_emby.playback import EmbyPlaybackProvider
from mopidy_emby.remote import EmbyHandler


logger = logging.getLogger(__name__)


class EmbyBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['emby']

    def __init__(self, config, audio):
        super(EmbyBackend, self).__init__()

        self.library = EmbyLibraryProvider(backend=self)
        self.playback = EmbyPlaybackProvider(audio=audio, backend=self)
        self.playlist = None
        self.remote = EmbyHandler(config)
