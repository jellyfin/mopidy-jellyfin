import mock

import mopidy

import pytest

import mopidy_jellyfin


@pytest.fixture
def config():
    return {
        'jellyfin': {
            'hostname': 'https://foo.bar',
            'port': 443,
            'username': 'jellyfinuser',
            'password': 'jellyfinpassword'
        },
        'proxy': {
            'foo': 'bar'
        }
    }


@pytest.fixture
def jellyfin_client(config, mocker):
    mocker.patch('mopidy_jellyfin.remote.cache')
    mocker.patch('mopidy_jellyfin.remote.JellyfinHandler._get_token')
    mocker.patch('mopidy_jellyfin.remote.JellyfinHandler._create_headers')
    mocker.patch('mopidy_jellyfin.remote.JellyfinHandler._get_user',
                 return_value=[{'Id': 'mock'}])
    mocker.patch('mopidy_jellyfin.remote.JellyfinHandler._password_data')

    return mopidy_jellyfin.remote.JellyfinHandler(config)


@pytest.fixture
def backend_mock():
    backend_mock = mock.Mock(autospec=mopidy_jellyfin.backend.JellyfinBackend)

    return backend_mock


@pytest.fixture
def libraryprovider(backend_mock):
    backend_mock.remote(autospec=mopidy_jellyfin.backend.JellyfinHandler)
    backend_mock.remote.get_artists.return_value = ['Artistlist']
    backend_mock.remote.get_albums.return_value = ['Albumlist']
    backend_mock.remote.get_tracks.return_value = ['Tracklist']
    backend_mock.remote.get_track.return_value = mopidy.models.Track(
        uri='jellyfin:track:eb6c305bdb1e40d3b46909473c22d906',
        name='The One With the Tambourine',
        track_no=1,
        genre=None,
        artists=[
            mopidy.models.Artist(
                name='American Football'
            )
        ],
        album=mopidy.models.Album(
            name='American Football',
            artists=[
                mopidy.models.Artist(
                    name='American Football'
                )
            ]
        ),
        length=2411620000 / 10000
    )
    backend_mock.remote.get_directory.return_value = {
        'Items': [
            {
                'Id': 123
            }
        ]
    }
    backend_mock.remote.lookup_artist.return_value = ['track1', 'track2']

    return mopidy_jellyfin.backend.JellyfinLibraryProvider(backend_mock)


@pytest.fixture
def playbackprovider(backend_mock, jellyfin_client):
    backend_mock.remote = jellyfin_client

    return mopidy_jellyfin.backend.JellyfinPlaybackProvider(audio=mock.Mock(),
                                                    backend=backend_mock)
