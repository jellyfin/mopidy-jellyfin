from __future__ import unicode_literals

from mock import patch
import json
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
@patch('mopidy_emby.backend.EmbyHandler._get_token')
@patch('mopidy_emby.backend.EmbyHandler._create_headers')
@patch('mopidy_emby.backend.EmbyHandler._get_user')
@patch('mopidy_emby.backend.EmbyHandler._password_data')
def test_get_music_root(password_data_mock, get_user_mock, create_header_mock,
                        get_token_mock, r_get_mock, config, data, expected):
    get_user_mock.return_value = [{'Id': 'foo'}]

    with open(data, 'r') as f:
        r_get_mock.return_value = json.load(f)

    emby = mopidy_emby.backend.EmbyHandler(config)

    assert emby.get_music_root() == expected
