from __future__ import unicode_literals

import mock

from mopidy_jellyfin import library, playback
from mopidy_jellyfin.backend import JellyfinBackend


@mock.patch('mopidy_jellyfin.backend.JellyfinHandler', autospec=True)
def test_backend(jellyfinhander_mock, config):
    backend = JellyfinBackend(config, mock.Mock())

    assert backend.uri_schemes == ['jellyfin']

    assert isinstance(backend.library, library.JellyfinLibraryProvider)
    assert isinstance(backend.playback, playback.JellyfinPlaybackProvider)
    assert backend.playlist is None
