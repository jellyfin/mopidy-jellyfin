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

        # Used for browsing artists in Iris
        if uri.startswith('jellyfin:artists'):
            artists = self.backend.remote.get_all_artists()
            return [self.backend.remote.get_artist_as_ref(artist)
                    for artist in artists]

        # Used for browsing albums in Iris
        if uri.startswith('jellyfin:albums'):
            albums = self.backend.remote.get_all_albums()
            return [self.backend.remote.get_album_as_ref(album)
                    for album in albums]

        # move one level lower in directory tree
        if uri.startswith('jellyfin:') and len(parts) == 3:
            item_id = parts[-1]
            return self.backend.remote.browse_item(item_id)

        return []

    def lookup(self, uri=None, uris=None):
        logger.debug('Jellyfin lookup: {}'.format(uri or uris))
        if uri:
            parts = uri.split(':')

            if uri.startswith('jellyfin:track:') and len(parts) == 3:
                track_id = parts[-1]
                contents = [self.backend.remote.get_track(track_id)]

            elif uri.startswith('jellyfin:album:') and len(parts) == 3:
                album_id = parts[-1]
                album_data = self.backend.remote.get_directory(album_id)
                contents = [
                    self.backend.remote.create_track(track)
                    for track in album_data.get('Items', [])
                    if track.get('Type') == 'Audio'
                ]

                contents = sorted(contents, key=lambda k: (k.track_no, k.name))

            elif uri.startswith('jellyfin:artist:') and len(parts) == 3:
                artist_id = parts[-1]

                contents = self.backend.remote.lookup_artist(artist_id)

            elif uri.startswith('jellyfin:directory:') or uri == 'jellyfin:':
                # Prevents weirdness when using Iris, this gets redirected to browse()
                contents = []

            else:
                logger.info('Unknown Jellyfin lookup URI: {}'.format(uri))
                contents = []

            return contents

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
            artists = self.backend.remote.get_all_artists()
            return [ artist.get('Name') for artist in artists ]
        elif field == 'album':
            albums = self.backend.remote.get_albums(query)
            return [album.get('Name') for album in albums]
        return []
