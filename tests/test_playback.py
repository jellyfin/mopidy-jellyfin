from __future__ import unicode_literals

import pytest


@pytest.mark.parametrize('uri,expected', [
    (
        'emby:track:123',
        'https://foo.bar:443/Audio/123/stream.mp3?format=json'
    ),
    (
        'emby:foobar',
        None
    )
])
def test_translate_uri(playbackprovider, uri, expected):
    assert playbackprovider.translate_uri(uri) == expected
