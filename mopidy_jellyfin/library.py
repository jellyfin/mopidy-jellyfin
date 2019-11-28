from __future__ import unicode_literals

import logging

from mopidy import backend, models


logger = logging.getLogger(__name__)


class JellyfinLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='jellyfin:',
                                          name='Jellyfin')

    def browse(self, uri):
        # display top level libraries
        if uri == self.root_directory.uri:
            logger.debug('Get Jellyfin library list')
            return self.backend.remote.get_library_roots()

        # split uri
        parts = uri.split(':')

        # move one level lower in directory tree
        if uri.startswith('jellyfin:') and len(parts) == 3:
            item_id = parts[-1]
            item_type = self.backend.remote.get_item(item_id).get('Type')
            return self.backend.remote.browse_item(item_id)

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
                    self.backend.remote.create_track(track)
                    for track in album_data.get('Items', [])
                ]

                tracks = sorted(tracks, key=lambda k: k.track_no)

            elif uri.startswith('jellyfin:artist:') and len(parts) == 3:
                artist_id = parts[-1]

                tracks = self.backend.remote.lookup_artist(artist_id)

            else:
                logger.info('Unknown Jellyfin lookup URI: {}'.format(uri))
                tracks = []

            return tracks

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}

    def search(self, query=None, uris=None, exact=False):
        logger.debug('Jellyfin Search Query: {}'.format(query))
        if exact:
            return self.backend.remote.exact_search(query)
        return self.backend.remote.search(query)

    def get_distinct(self, field, query=None):
        # Populates Media Library sections (Artists, Albums, etc)
        # Mopidy internally calls search() with exact=True
        if field == 'artist' or field == 'albumartist':
            return [
                artist.name for artist in self.backend.remote.get_artists()
            ]
        elif field == 'album':
            return [
                album.name for album in self.backend.remote.get_albums(query)
            ]
        return []
