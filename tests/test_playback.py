from __future__ import unicode_literals

import pytest


@pytest.mark.parametrize('uri,expected', [
    (
        'jellyfin:track:123',
        [
            'https://foo.bar:443/Audio/123/stream?static=true&format=json',
            'https://foo.bar:443/Audio/123/stream?format=json&static=true',
        ]
    ),
    (
        'jellyfin:foobar',
        [None]
    )
])
def test_translate_uri(playbackprovider, uri, expected):
    assert playbackprovider.translate_uri(uri) in expected
