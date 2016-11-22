from __future__ import unicode_literals

import logging

from mopidy import backend, models


logger = logging.getLogger(__name__)


class EmbyLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='emby:',
                                          name='Emby')

    def browse(self, uri):
        if uri == self.root_directory.uri:
            music_root = self.backend.remote.get_music_root()
            artists = sorted(
                self.backend.remote.get_directory(music_root)['Items'],
                key=lambda k: k['Name']
            )
            return [
                models.Ref.artist(
                    uri='emby:{}'.format(i['Id']),
                    name=i['Name']
                )
                for i in artists
            ]

        # split uri
        parts = uri.split(':')

        # albums
        if len(parts) == 2:
            id = parts[1]
            albums = sorted(
                self.backend.remote.get_directory(id)['Items'],
                key=lambda k: k['Name']
            )
            return [
                models.Ref.album(
                    uri='emby:{}:{}'.format(id, i['Id']),
                    name=i['Name']
                )
                for i in albums
            ]

        # tracklist
        if len(parts) == 3:
            id = parts[2]
            tracks = sorted(
                self.backend.remote.get_directory(id)['Items']
            )
            return [
                models.Ref.track(
                    uri='emby:{}:{}:{}'.format(id, parts[1], i['Id']),
                    name=i['Name']
                )
                for i in tracks
            ]

        return []

    def lookup(self, uri=None, uris=None):
        logger.debug('Emby lookup: {}'.format(uri or uris))
        if uri:
            parts = uri.split(':')
            logger.debug('Emby lookup: {}'.format(uri))

            if len(parts) == 3:
                tracks = self.backend.remote.get_album_tracks(uri)

            elif len(parts) == 4:
                tracks = [self.backend.remote.get_track(uri)]

            else:
                logger.info('Unknown Emby lookup URI: '.format(uri))
                tracks = []

            return [track for track in tracks if track]

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}
