from __future__ import unicode_literals

import json

import mock

from mopidy.models import Album, Artist, Ref, SearchResult, Track

import pytest

import requests

from mopidy_emby import backend


@pytest.mark.parametrize('hostname,url,expected', [
    ('https://foo.bar', '/Foo', 'https://foo.bar:443/Foo?format=json'),
    ('foo.bar', '/Foo', 'http://foo.bar:443/Foo?format=json'),
])
@mock.patch('mopidy_emby.backend.EmbyHandler._get_token')
@mock.patch('mopidy_emby.backend.EmbyHandler._create_headers')
@mock.patch('mopidy_emby.backend.EmbyHandler._get_user')
@mock.patch('mopidy_emby.backend.EmbyHandler._password_data')
def test_api_url(password_data_mock, get_user_mock, create_header_mock,
                 get_token_mock, config, hostname, url, expected):
    get_user_mock.return_value = [{'Id': 'foo'}]

    config['emby']['hostname'] = hostname
    emby = backend.EmbyHandler(config)

    assert emby.api_url(url) == expected


@pytest.mark.parametrize('data,expected', [
    ('tests/data/get_music_root0.json', 'eb169f4ba53fc560f549cb0f2a47d577')
])
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_music_root(r_get_mock, data, expected, emby_client):

    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_music_root() == expected


@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/get_music_root1.json',
        'Emby: Cant find music root directory'
    )
])
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_music_root_cant_find(r_get_mock, data, expected, emby_client):

    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    with pytest.raises(Exception) as execinfo:
        print emby_client.get_music_root()

    assert expected in str(execinfo.value)


@mock.patch('mopidy_emby.backend.EmbyHandler.get_music_root')
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_artists(r_get_mock, get_music_root_mock, emby_client):
    expected = [
        Ref(name=u'Chairlift',
            type='artist',
            uri='emby:artist:e0361aff955c30f5a6dcc6fcf0c9d1cf'),
        Ref(name=u'Hans Zimmer',
            type='artist',
            uri='emby:artist:36de3368f493ebca94a55a411cc87862'),
        Ref(name=u'The Menzingers',
            type='artist',
            uri='emby:artist:21c8f78763231ece7defd07b5f3f56be')
    ]

    with open('tests/data/get_artists0.json', 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_artists() == expected


@mock.patch('mopidy_emby.backend.EmbyHandler.get_music_root')
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_albums(r_get_mock, get_music_root_mock, emby_client):
    expected = [
        Ref(name=u'American Football',
            type='album',
            uri='emby:album:6e4a2da7df0502650bb9b091312c3dbf'),
        Ref(name=u'American Football',
            type='album',
            uri='emby:album:ca498ea939b28593744c051d9f5e74ed'),
        Ref(name=u'American Football',
            type='album',
            uri='emby:album:0db6395ab76b6edbaba3a51ef23d0aa3')
    ]

    with open('tests/data/get_albums0.json', 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_albums(0) == expected


@mock.patch('mopidy_emby.backend.EmbyHandler.get_music_root')
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_tracks(r_get_mock, get_music_root_mock, emby_client):
    expected = [
        Ref(name=u'The One With the Tambourine',
            type='track',
            uri='emby:track:eb6c305bdb1e40d3b46909473c22d906'),
        Ref(name=u'Letters and Packages',
            type='track',
            uri='emby:track:7739d3830818c7aacf6c346172384914'),
        Ref(name=u'Five Silent Miles',
            type='track',
            uri='emby:track:f84df9f70e592a3abda82b1d78026608')
    ]

    with open('tests/data/get_tracks0.json', 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_tracks(0) == expected


@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        Track(
            album=Album(artists=[Artist(name=u'Chairlift')], name=u'Moth'),
            artists=[Artist(name=u'Chairlift')],
            length=295915,
            name=u'Ottawa to Osaka',
            track_no=6,
            uri='emby:track:18e5a9871e6a4a2294d5af998457ca16'
        )
     ),
    (
        'tests/data/track1.json',
        Track(
            album=Album(artists=[Artist(name=u'Chairlift')], name=u'Moth'),
            artists=[Artist(name=u'Chairlift')],
            length=269035,
            name=u'Crying in Public',
            track_no=5,
            uri='emby:track:37f57f0b370274af96de06895a78c2c3'
         )
     ),
    (
        'tests/data/track2.json',
        Track(
            album=Album(artists=[Artist(name=u'Chairlift')], name=u'Moth'),
            artists=[Artist(name=u'Chairlift')],
            length=283115,
            name=u'Polymorphing',
            track_no=2,
            uri='emby:track:3315cccffe37ab47d50d1dbeefd3537b'
        )
    ),
])
def test_create_track(data, expected, emby_client):
    with open(data, 'r') as f:
        track = json.load(f)

    assert emby_client.create_track(track) == expected


@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        Album(artists=[Artist(name=u'Chairlift')], name=u'Moth')
    ),
    (
        'tests/data/track1.json',
        Album(artists=[Artist(name=u'Chairlift')], name=u'Moth')
    ),
    (
        'tests/data/track2.json',
        Album(artists=[Artist(name=u'Chairlift')], name=u'Moth')
    ),
])
def test_create_album(data, expected, emby_client):
    with open(data, 'r') as f:
        track = json.load(f)

    assert emby_client.create_album(track) == expected


@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        [Artist(name=u'Chairlift')]
    ),
    (
        'tests/data/track1.json',
        [Artist(name=u'Chairlift')]
    ),
    (
        'tests/data/track2.json',
        [Artist(name=u'Chairlift')]
    ),
])
def test_create_artists(data, expected, emby_client):
    with open(data, 'r') as f:
        track = json.load(f)

    assert emby_client.create_artists(track) == expected


@pytest.mark.parametrize('data,user_id', [
    ('tests/data/get_user0.json', '2ec276a2642e54a19b612b9418a8bd3b')
])
@mock.patch('mopidy_emby.remote.requests.get')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_token')
@mock.patch('mopidy_emby.remote.EmbyHandler._create_headers')
@mock.patch('mopidy_emby.remote.EmbyHandler._password_data')
def test_get_user(password_mock, create_headers_mock, get_tocken_mock,
                  get_mock, data, user_id, config):

    mock_response = mock.Mock()
    with open(data, 'r') as f:
        mock_response.json.return_value = json.load(f)

    get_mock.return_value = mock_response

    emby = backend.EmbyHandler(config)

    assert emby.user_id == user_id


@mock.patch('mopidy_emby.remote.requests.get')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_token')
@mock.patch('mopidy_emby.remote.EmbyHandler._create_headers')
@mock.patch('mopidy_emby.remote.EmbyHandler._password_data')
def test_get_user_exception(password_mock, create_headers_mock,
                            get_tocken_mock, get_mock, config):

    mock_response = mock.Mock()
    with open('tests/data/get_user1.json', 'r') as f:
        mock_response.json.return_value = json.load(f)

    get_mock.return_value = mock_response

    with pytest.raises(Exception) as execinfo:
        backend.EmbyHandler(config)

    assert 'No Emby user embyuser found' in str(execinfo.value)


@pytest.mark.parametrize('data,token', [
    ('tests/data/get_token0.json', 'f0d6b372b40b47299ed01b9b2d40489b'),
    ('tests/data/get_token1.json', None),
])
@mock.patch('mopidy_emby.remote.requests.post')
@mock.patch('mopidy_emby.remote.EmbyHandler._create_headers')
@mock.patch('mopidy_emby.remote.EmbyHandler._password_data')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_user')
def test_get_token(get_user_mock, password_data_mock,
                   create_headers_mock, post_mock, data,
                   token, config):

    mock_response = mock.Mock()
    with open(data, 'r') as f:
        mock_response.json.return_value = json.load(f)

    post_mock.return_value = mock_response

    emby = backend.EmbyHandler(config)

    assert emby.token == token


@mock.patch('mopidy_emby.remote.requests')
@mock.patch('mopidy_emby.remote.EmbyHandler._create_headers')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_user')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_token')
def test_password_data(get_token_mock, get_user_mock, create_headers_mock,
                       requests_mock, config):

    emby = backend.EmbyHandler(config)

    assert emby._password_data() == {
        'username': 'embyuser',
        'password': '444b73bcd9dc4331104c5ef960ee240066f8a3e5',
        'passwordMd5': '1d549a7b47c46b7b0a90651360c5574c'
    }


@pytest.mark.parametrize('token,headers', [
    (
        None,
        {
            'x-emby-authorization': ('MediaBrowser UserId="123", '
                                     'Client="other", Device="mopidy", '
                                     'DeviceId="mopidy", Version="0.0.0"')
        }
    ),
    (
        'f0d6b372b40b47299ed01b9b2d40489b',
        {
            'x-emby-authorization': ('MediaBrowser UserId="123", '
                                     'Client="other", Device="mopidy", '
                                     'DeviceId="mopidy", Version="0.0.0"'),
            'x-mediabrowser-token': 'f0d6b372b40b47299ed01b9b2d40489b'
        }
    )
])
@mock.patch('mopidy_emby.remote.requests')
@mock.patch('mopidy_emby.remote.EmbyHandler._password_data')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_user')
@mock.patch('mopidy_emby.remote.EmbyHandler._get_token')
def test_create_headers(get_token_mock, get_user_mock, password_data_mock,
                        requests_mock, token, headers, config):

    get_user_mock.return_value = [{'Id': 123}]
    get_token_mock.return_value = token

    emby = backend.EmbyHandler(config)

    assert emby.headers == headers


@pytest.mark.parametrize('query,data,expected', [
    (
        {'track_name': ['viva hate']},
        'tests/data/search_audio0.json',
        SearchResult(
            tracks=[
                Track(
                    album=Album(
                        artists=[Artist(name=u'Rainer Maria')],
                        name=u'Past Worn Searching'
                    ),
                    artists=[Artist(name=u'Rainer Maria')],
                    name='Viva Anger, Viva Hate',
                    track_no=3,
                    uri='emby:track:b5d600663238be5b41da4d8429db85f0'
                )
            ],
            uri='emby:search'
        )
    ),
    (
        {'album': ['viva hate']},
        'tests/data/search_album0.json',
        SearchResult(
            albums=[
                Album(
                    artists=[Artist(name=u'Morrissey')],
                    name=u'Viva Hate',
                    uri='emby:album:4bf594cb601ec46a0295729c4d0f7f80')
            ],
            uri='emby:search'
        )
    ),
    (
        {'artist': ['morrissey']},
        'tests/data/search_artist0.json',
        SearchResult(
            artists=[
                Artist(
                    name=u'Morrissey',
                    uri='emby:artist:0b74a057d86092f48698be681737c4ed'
                ),
                Artist(
                    name=u'Morrissey & Siouxsie Sioux',
                    uri='emby:artist:32bbd3db105255b24a83d0d955179dc4'
                ),
                Artist(
                    name=u'Morrissey & Siouxsie Sioux',
                    uri='emby:artist:eb69a3f2db13691d24c6a9794926ddb8'
                )
            ],
            uri='emby:search'
        )
    )
])
@mock.patch('mopidy_emby.backend.EmbyHandler._get_search')
def test_search(get_search_mock, query, data, expected, emby_client):
    with open(data, 'r') as f:
        get_search_mock.return_value = json.load(f)['SearchHints']

    assert emby_client.search(query) == expected


@mock.patch('mopidy_emby.backend.EmbyHandler._get_session')
def test_r_get(session_mock, emby_client):
    data = {'foo': 'bar'}
    session_mock.return_value.get.return_value.json.return_value = data

    assert emby_client.r_get('http://foo.bar') == data


@mock.patch('mopidy_emby.remote.EmbyHandler._get_session')
def test_r_get_exception(session_mock, emby_client):
    session_mock.return_value.get.side_effect = Exception()

    with pytest.raises(Exception) as execinfo:
        emby_client.r_get('http://foo.bar')

    assert 'Cant connect to Emby API' in str(execinfo.value)


@pytest.mark.parametrize('ticks,milliseconds', [
    (2010380000, 201038),
    (2508020000, 250802),
])
def test_ticks_to_milliseconds(ticks, milliseconds, emby_client):
    assert emby_client.ticks_to_milliseconds(ticks) == milliseconds


@pytest.mark.parametrize('milliseconds,ticks', [
    (201038, 2010380000),
    (250802, 2508020000),
])
def test_milliseconds_to_ticks(milliseconds, ticks, emby_client):
    assert emby_client.milliseconds_to_ticks(milliseconds) == ticks


def test__get_session(emby_client):
    assert isinstance(emby_client._get_session(), requests.sessions.Session)


@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        [
            'Album',
            'Genres',
        ]
    )
])
def test_get_item(r_get_mock, data, expected, emby_client):
    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    item_keys = emby_client.get_item(0).keys()

    for key in expected:
        assert key in item_keys


@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        Track(
            album=Album(artists=[Artist(name=u'Chairlift')], name=u'Moth'),
            artists=[Artist(name=u'Chairlift')],
            length=295915,
            name=u'Ottawa to Osaka',
            track_no=6,
            uri='emby:track:18e5a9871e6a4a2294d5af998457ca16'
        )
    )
])
def test_get_track(r_get_mock, data, expected, emby_client):
    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_track(0) == expected


@pytest.mark.parametrize('itemtype,url', [
    (
        'any',
        ('/Search/Hints?SearchTerm=viva%20hate'
         '&IncludeItemTypes=Audio,MusicAlbum,MusicArtist')
    ),
    (
        'artist',
        ('/Search/Hints?SearchTerm=viva%20hate'
         '&IncludeItemTypes=MusicArtist')
    ),
    (
        'album',
        ('/Search/Hints?SearchTerm=viva%20hate'
         '&IncludeItemTypes=MusicAlbum')
    ),
    (
        'track_name',
        ('/Search/Hints?SearchTerm=viva%20hate'
         '&IncludeItemTypes=Audio')
    ),
])
@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
@mock.patch('mopidy_emby.backend.EmbyHandler.api_url')
def test__get_search(api_url_mock, r_get_mock, itemtype, url, emby_client):
    with open('tests/data/search_audio0.json', 'r') as f:
        r_get_mock.return_value = json.load(f)

    emby_client._get_search(itemtype, 'viva hate')

    api_url_mock.assert_called_with(url)


@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test__get_search_exception(r_get_mock, emby_client):
    with pytest.raises(Exception) as execinfo:
        emby_client._get_search('foo', 'bar')

    assert 'Emby search: no itemtype foo' in str(execinfo.value)


@mock.patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_lookup_artist(r_get_mock, emby_client):
    with open('tests/data/lookup_artist0.json', 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.lookup_artist(0) == [
        Track(
            album=Album(
                artists=[Artist(name=u'Jawbreaker')],
                name=u'24 Hour Revenge Therapy'
            ),
            artists=[
                Artist(
                    name=u'Jawbreaker'
                )
            ],
            length=159840,
            name=u'The Boat Dreams From The Hill',
            track_no=1,
            uri='emby:track:05321ccb30ff9e43bf8070cd5f70c783'
        ),
        Track(
            album=Album(
                artists=[Artist(name=u'Jawbreaker')],
                name=u'Dear You'
            ),
            artists=[
                Artist(
                    name=u'Jawbreaker'
                )
            ],
            length=131133,
            name=u'Bad Scene, Everyone\u2019s Fault',
            track_no=10,
            uri='emby:track:0a24ce6c243f2f3a81fa0f99625630b4'
        ),
        Track(
            album=Album(
                artists=[Artist(name=u'Jawbreaker')],
                name=u'Dear You'
            ),
            artists=[
                Artist(
                    name=u'Jawbreaker'
                )
            ],
            length=254107,
            name=u'Sluttering (May 4th)',
            track_no=11,
            uri='emby:track:057801bc10cf08ce96e1e19bf98c407f'
        )
     ]
