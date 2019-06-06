from __future__ import unicode_literals

import logging

from mopidy import backend

import pykka

from mopidy_jellyfin.library import JellyfinLibraryProvider
from mopidy_jellyfin.playback import JellyfinPlaybackProvider
from mopidy_jellyfin.remote import JellyfinHandler
from mopidy_jellyfin.playlists import JellyfinPlaylistsProvider


logger = logging.getLogger(__name__)


class JellyfinBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['jellyfin']

    def __init__(self, config, audio):
        super(JellyfinBackend, self).__init__()

        self.library = JellyfinLibraryProvider(backend=self)
        self.playback = JellyfinPlaybackProvider(audio=audio, backend=self)
        self.remote = JellyfinHandler(config)
        self.playlists = JellyfinPlaylistsProvider(backend=self)
