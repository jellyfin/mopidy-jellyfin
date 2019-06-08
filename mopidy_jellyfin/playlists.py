from __future__ import unicode_literals

import logging
import operator
import time

from mopidy import backend
from mopidy.models import Playlist, Ref

logger = logging.getLogger(__name__)

class JellyfinPlaylistsProvider(backend.PlaylistsProvider):

    def __init__(self, *args, **kwargs):
        super(JellyfinPlaylistsProvider, self).__init__(*args, **kwargs)
        self._playlists = {}
        self.refresh()

    def as_list(self):
        self.refresh()
        refs = [
            Ref.playlist(uri=i.uri, name=i.name)
            for i in self._playlists.values()]
        return sorted(refs, key=operator.attrgetter('name'))

    def get_items(self, uri):
        self.refresh()
        playlist = self._playlists.get(uri)
        if not playlist:
            logger.info('Jellyfin: No playlists found')
            return None
        return [Ref.track(uri=i.uri, name=i.name) for i in playlist.tracks]

    def lookup(self, uri):
        return self._playlists.get(uri)

    def refresh(self):
        playlists = {}

        raw_playlists = self.backend.remote.get_playlists()
        if raw_playlists:
            for playlist in raw_playlists:
                playlist_id = playlist.uri.split(':')[-1]
                contents = self.backend.remote.get_playlist_contents(playlist_id)
                tracks = [
                    self.backend.remote.get_track(track['Id'])
                    for track in contents
                ]
                playlists[playlist.uri] = Playlist(
                    uri=playlist.uri,
                    name=playlist.name,
                    tracks=tracks
                )

        self._playlists = playlists
        backend.BackendListener.send('playlists_loaded')


        return []

    def create(self, name):
        playlist = self.backend.remote.create_playlist(name)
        self.refresh()

        return Playlist(
            uri='jellyfin:playlists:{}'.format(playlist['Id']),
            name=name,
            tracks=[]
        )

    def delete(self, uri):
        playlist_id = uri.split(':')[-1]
        result = self.backend.remote.delete_playlist(playlist_id)

        if not result:
            del self._playlists[uri]
            self.refresh()
            return True
        return False

    def save(self, playlist):
        playlist_id = playlist.uri.split(':')[-1]

        new_track_ids = [
            i.uri.split(':')[-1] for i in playlist.tracks
        ]

        data = self.backend.remote.update_playlist(
            playlist_id, new_track_ids
        )

        return Playlist(
            uri=playlist.uri,
            name=playlist.name,
            tracks=playlist.tracks
        )
