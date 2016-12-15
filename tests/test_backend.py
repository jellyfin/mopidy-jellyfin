from __future__ import unicode_literals

import mock

from mopidy_emby import library, playback
from mopidy_emby.backend import EmbyBackend


@mock.patch('mopidy_emby.backend.EmbyHandler', autospec=True)
def test_backend(embyhander_mock, config):
    backend = EmbyBackend(config, mock.Mock())

    assert backend.uri_schemes == ['emby']

    assert isinstance(backend.library, library.EmbyLibraryProvider)
    assert isinstance(backend.playback, playback.EmbyPlaybackProvider)
    assert backend.playlist is None
