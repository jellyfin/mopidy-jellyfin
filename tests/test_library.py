from __future__ import unicode_literals

from mopidy.models import Album, Artist, Track

import pytest


@pytest.mark.parametrize('uri,expected', [
    ('emby:', ['Artistlist']),
    ('emby:artist:123', ['Albumlist']),
    ('emby:album:123', ['Tracklist']),
])
def test_browse(uri, expected, libraryprovider):
    assert libraryprovider.browse(uri) == expected


@pytest.mark.parametrize('uri,expected', [
    ('emby:track:123', [
        Track(
            album=Album(
                artists=[
                    Artist(name='American Football')
                ],
                name='American Football'),
            artists=[Artist(name='American Football')],
            length=241162,
            name='The One With the Tambourine',
            track_no=1,
            uri='emby:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]),
    ('emby:album:123', [
        Track(
            album=Album(
                artists=[
                    Artist(name='American Football')
                ],
                name='American Football'),
            artists=[Artist(name='American Football')],
            length=241162,
            name='The One With the Tambourine',
            track_no=1,
            uri='emby:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]),
    ('emby:artist:123', ['track1', 'track2']),
    ('emby:track', [])
])
def test_lookup_uri(uri, expected, libraryprovider):
    assert libraryprovider.lookup(uri=uri) == expected


@pytest.mark.parametrize('uri,expected', [
    (['emby:track:123'], {'emby:track:123': [
        Track(
            album=Album(
                artists=[
                    Artist(name='American Football')
                ],
                name='American Football'),
            artists=[Artist(name='American Football')],
            length=241162,
            name='The One With the Tambourine',
            track_no=1,
            uri='emby:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]}),
    (['emby:track'], {u'emby:track': []})
])
def test_lookup_uris(uri, expected, libraryprovider):
    assert libraryprovider.lookup(uris=uri) == expected
