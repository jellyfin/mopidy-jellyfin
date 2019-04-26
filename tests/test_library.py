from __future__ import unicode_literals

from mopidy.models import Album, Artist, Track

import pytest


@pytest.mark.parametrize('uri,expected', [
    ('jellyfin:', ['Artistlist']),
    ('jellyfin:artist:123', ['Albumlist']),
    ('jellyfin:album:123', ['Tracklist']),
])
def test_browse(uri, expected, libraryprovider):
    assert libraryprovider.browse(uri) == expected


@pytest.mark.parametrize('uri,expected', [
    ('jellyfin:track:123', [
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
            uri='jellyfin:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]),
    ('jellyfin:album:123', [
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
            uri='jellyfin:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]),
    ('jellyfin:artist:123', ['track1', 'track2']),
    ('jellyfin:track', [])
])
def test_lookup_uri(uri, expected, libraryprovider):
    assert libraryprovider.lookup(uri=uri) == expected


@pytest.mark.parametrize('uri,expected', [
    (['jellyfin:track:123'], {'jellyfin:track:123': [
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
            uri='jellyfin:track:eb6c305bdb1e40d3b46909473c22d906'
        )
    ]}),
    (['jellyfin:track'], {u'jellyfin:track': []})
])
def test_lookup_uris(uri, expected, libraryprovider):
    assert libraryprovider.lookup(uris=uri) == expected
