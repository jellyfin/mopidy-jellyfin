from __future__ import unicode_literals

import logging

from mopidy import backend, models


logger = logging.getLogger(__name__)


class JellyfinLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='jellyfin:',
                                          name='Jellyfin')

    def browse(self, uri):
        # artistlist
        if uri == self.root_directory.uri:
            logger.debug('Get Jellyfin artist list')
            return self.backend.remote.get_artists()

        # split uri
        parts = uri.split(':')

        # artists albums
        # uri: jellyfin:artist:<artist_id>
        if uri.startswith('jellyfin:artist:') and len(parts) == 3:
            logger.debug('Get Jellyfin album list')
            artist_id = parts[-1]

            return self.backend.remote.get_albums(artist_id)

        # tracklist
        # uri: jellyfin:album:<album_id>
        if uri.startswith('jellyfin:album:') and len(parts) == 3:
            logger.debug('Get Jellyfin track list')
            album_id = parts[-1]

            return self.backend.remote.get_tracks(album_id)

        return []

    def lookup(self, uri=None, uris=None):
        logger.debug('Jellyfin lookup: {}'.format(uri or uris))
        if uri:
            parts = uri.split(':')

            if uri.startswith('jellyfin:track:') and len(parts) == 3:
                track_id = parts[-1]
                tracks = [self.backend.remote.get_track(track_id)]

            elif uri.startswith('jellyfin:album:') and len(parts) == 3:
                album_id = parts[-1]
                album_data = self.backend.remote.get_directory(album_id)
                tracks = [
                    self.backend.remote.get_track(i['Id'])
                    for i in album_data.get('Items', [])
                ]

                tracks = sorted(tracks, key=lambda k: k.track_no)

            elif uri.startswith('jellyfin:artist:') and len(parts) == 3:
                artist_id = parts[-1]

                tracks = self.backend.remote.lookup_artist(artist_id)

            else:
                logger.info('Unknown Jellyfin lookup URI: {}'.format(uri))
                tracks = []

            return [track for track in tracks if track]

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}

    def search(self, query=None, uris=None, exact=False):
        return self.backend.remote.search(query)
