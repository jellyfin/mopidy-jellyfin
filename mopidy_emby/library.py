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
                self.backend.remote.get_item(music_root)['Items'],
                key=lambda k: k['Name']
            )
            return [
                models.Ref.directory(
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
            return [
                models.Ref.directory(
                    uri='emby:{}:{}'.format(id, i['Id']),
                    name=i['Name']
                )
                for i in self.backend.remote.get_item(id)['Items']
            ]

        return []
