from __future__ import unicode_literals

import json

from mock import patch

from mopidy.models import Album, Artist, Track

import pytest

import mopidy_emby


def test_get_default_config():
    ext = mopidy_emby.Extension()

    config = ext.get_default_config()

    assert '[emby]' in config
    assert 'enabled = true' in config


def test_get_config_schema():
    ext = mopidy_emby.Extension()

    schema = ext.get_config_schema()

    assert 'username' in schema
    assert 'password' in schema
    assert 'hostname' in schema
    assert 'port' in schema


@pytest.mark.parametrize('hostname,url,expected', [
    ('https://foo.bar', '/Foo', 'https://foo.bar:443/Foo?format=json'),
    ('foo.bar', '/Foo', 'http://foo.bar:443/Foo?format=json'),
])
@patch('mopidy_emby.backend.EmbyHandler._get_token')
@patch('mopidy_emby.backend.EmbyHandler._create_headers')
@patch('mopidy_emby.backend.EmbyHandler._get_user')
@patch('mopidy_emby.backend.EmbyHandler._password_data')
def test_api_url(password_data_mock, get_user_mock, create_header_mock,
                 get_token_mock, config, hostname, url, expected):
    get_user_mock.return_value = [{'Id': 'foo'}]

    config['emby']['hostname'] = hostname
    emby = mopidy_emby.backend.EmbyHandler(config)

    assert emby.api_url(url) == expected


@pytest.mark.parametrize('data,expected', [
    ('tests/data/get_music_root0.json', 'eb169f4ba53fc560f549cb0f2a47d577')
])
@patch('mopidy_emby.backend.EmbyHandler.r_get')
def test_get_music_root(r_get_mock, data, expected, emby_client):

    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    assert emby_client.get_music_root() == expected


@pytest.mark.parametrize('data,expected', [
    (
        'tests/data/track0.json',
        Track(
            album=Album(artists=[Artist(name=u'Chairlift')], name=u'Moth'),
            artists=[Artist(name=u'Chairlift')],
            length=295915,
            name=u'Ottawa to Osaka',
            track_no=6,
            uri='emby::18e5a9871e6a4a2294d5af998457ca16'
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
            uri='emby::37f57f0b370274af96de06895a78c2c3'
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
            uri='emby::3315cccffe37ab47d50d1dbeefd3537b'
        )
    ),
])
def test_create_track(data, expected, emby_client):
    with open(data, 'r') as f:
        track = json.load(f)

    assert emby_client.create_track('emby:', track) == expected
