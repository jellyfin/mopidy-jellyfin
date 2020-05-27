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
        if not playlist:
            logger.info('Jellyfin: No playlists found')
            return None

        return [Ref.track(uri=i.uri, name=i.name) for i in playlist.tracks]

    def lookup(self, uri):
        playlist = self._playlists.get(uri)

        return Playlist(
            uri=playlist.uri,
            name=playlist.name,
            tracks=playlist.tracks
        )

    def refresh(self):
        playlists = {}

        raw_playlists = self.backend.remote.get_playlists()
        if raw_playlists:
            for playlist in raw_playlists:
                playlist_id = playlist.get('Id')
                playlist_uri = 'jellyfin:playlist:%s' % playlist.get('Id')
                contents = self.backend.remote.get_playlist_contents(
                    playlist_id
                )
                # Create local Mopidy tracks for audio and book files
                tracks = [
                    self.backend.remote.create_track(track)
                    for track in contents if track['Type'] in ['Audio', 'Book']
                ]
                # Only create a playlist if it has valid tracks
                if tracks:
                    playlists[playlist_uri] = Playlist(
                        uri='jellyfin:playlist:%s' % playlist.get('Id'),
                        name=playlist.get('Name'),
                        tracks=tracks
                    )

        self._playlists = playlists
        backend.BackendListener.send('playlists_loaded')

        return []

    def create(self, name):
        playlist = self.backend.remote.create_playlist(name)
        self.refresh()

        return Playlist(
            uri='jellyfin:playlists:{}'.format(playlist.get('Id')),
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
        # Update modifications to the playlist in the Jellyfin server
        playlist_id = playlist.uri.split(':')[-1]

        # Get the list of Jellyfin Ids for each track of the playlist
        new_track_ids = [
            i.uri.split(':')[-1] for i in playlist.tracks
        ]

        self.backend.remote.update_playlist(
            playlist_id, new_track_ids
        )

        # Update the playlist views
        self.refresh()
        return playlist
