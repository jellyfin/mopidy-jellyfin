from __future__ import unicode_literals

import logging
import operator

from mopidy import backend
from mopidy.models import Playlist, Ref

logger = logging.getLogger(__name__)

class JellyfinPlaylistsProvider(backend.PlaylistsProvider):

    def __init__(self, *args, **kwargs):
        super(JellyfinPlaylistsProvider, self).__init__(*args, **kwargs)
        self._playlists = {}
        self.refresh()

    def as_list(self):
        refs = [
            Ref.playlist(uri=i.uri, name=i.name)
            for i in self._playlists.values()]
        return sorted(refs, key=operator.attrgetter('name'))

    def get_items(self, uri):
        playlist = self._playlists.get(uri)
        if playlist is None:
            logger.info('No playlist')
            return None
        return [Ref.track(uri=i.uri, name=i.name) for i in playlist.tracks]

    def lookup(self, uri):
        return self._playlists.get(uri)

    def refresh(self):
        playlists = {}

        raw_playlists = self.backend.remote.get_playlists()
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
        raise NotImplementedError

    def delete(self, uri):
        raise NotImplementedError

    def save(self, playlist):
        raise NotImplementedError
