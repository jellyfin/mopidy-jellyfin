from __future__ import unicode_literals

import logging

from mopidy import backend


logger = logging.getLogger(__name__)


class JellyfinPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, config, audio, backend):
        self.audio = audio
        self.backend = backend
        self.transcode = config.get('jellyfin').get('transcode')
        if self.transcode is None:
            self.transcode = False
        super().__init__(audio, backend)

    def translate_uri(self, uri):
        if uri.startswith('jellyfin:track:') and len(uri.split(':')) == 3:
            id = uri.split(':')[-1]

            if self.transcode:
                track_url = self.backend.remote.api_url('/Audio/{}/stream?Container=ogg'.format(id))
            else:
                track_url = self.backend.remote.api_url('/Audio/{}/stream?static=true'.format(id))

            logger.debug('Jellyfin track streaming url: {}'.format(track_url))

            return track_url

        else:
            return None
