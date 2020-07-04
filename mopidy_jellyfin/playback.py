from __future__ import unicode_literals

import logging
import random
import string

from mopidy import backend
import mopidy_jellyfin


logger = logging.getLogger(__name__)


class JellyfinPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, audio, backend):
        super(JellyfinPlaybackProvider, self).__init__(audio, backend)

    def translate_uri(self, uri):
        if uri.startswith('jellyfin:track:') and len(uri.split(':')) == 3:
            item_id = uri.split(':')[-1]
            # Build unique session ID
            letters = string.ascii_letters
            session_id = ''.join(random.choice(letters) for _ in range(20))
            # List of supported containers
            container = 'opus,mp3,aac,m4a,flac,webma,webm,wav,ogg,mpa,wma'
            bitrate = self.backend.remote.max_bitrate

            url_params = {
                'MaxStreamingBitrate': bitrate,
                'api_key': self.backend.remote.token,
                'UserId': self.backend.remote.user_id,
                'DeviceId': mopidy_jellyfin.Extension.device_id,
                'PlaySessionId': session_id,
                'TranscodingProtocol': 'hls',
                'Container': container,
                'AudioCodec': 'aac'
            }

            track_url = self.backend.remote.api_url(
                f'/Audio/{item_id}/universal', url_params)

            logger.debug('Jellyfin track streaming url: {}'.format(track_url))

            return track_url

        else:
            return None
