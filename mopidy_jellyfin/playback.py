from __future__ import unicode_literals

import logging

from mopidy import backend


logger = logging.getLogger(__name__)


class JellyfinPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        if uri.startswith('jellyfin:track:') and len(uri.split(':')) == 3:
            id = uri.split(':')[-1]

            url_params = { 'static': 'true' }
            track_url = self.backend.remote.api_url(
                '/Audio/{}/stream'.format(id), url_params
            )

            logger.debug('Jellyfin track streaming url: {}'.format(track_url))

            return track_url

        else:
            return None
