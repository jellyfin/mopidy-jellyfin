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
        self.playback = EmbyPlaybackProvider(audio=audio, backend=self)
        self.playlist = None
        self.remote = EmbyHandler(config['emby'])


class EmbyPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        id = uri.split(':')[-1]

        track_url = self.backend.remote.api_url(
            '/Audio/{}/stream.mp3'.format(id)
        )

        logger.debug('Emby track streaming url: {}'.format(track_url))

        return track_url
