import pytest

import mopidy_emby


@pytest.fixture
def config():
    return {
        'emby': {
            'hostname': 'https://foo.bar',
            'port': 443,
            'username': 'embyuser',
            'password': 'embypassword'
        },
        'proxy': {
            'foo': 'bar'
        }
    }


@pytest.fixture
def emby_client(config, mocker):
    mocker.patch('mopidy_emby.backend.EmbyHandler._get_token')
    mocker.patch('mopidy_emby.backend.EmbyHandler._create_headers')
    mocker.patch('mopidy_emby.backend.EmbyHandler._get_user',
                 return_value=[{'Id': 'mock'}])
    mocker.patch('mopidy_emby.backend.EmbyHandler._password_data')

    return mopidy_emby.backend.EmbyHandler(config)
