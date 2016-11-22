from __future__ import unicode_literals

import hashlib
import logging
import pykka
import requests

from urlparse import urljoin, urlsplit, parse_qs, urlunsplit
from urllib import urlencode

from mopidy import backend, models


logger = logging.getLogger(__name__)


class EmbyBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['emby']

    def __init__(self, config, audio):
        super(EmbyBackend, self).__init__()

        self.library = EmbyLibraryProvider(backend=self)
        self.playback = EmbyPlaybackProvider(audio=audio, backend=self)
        self.playlist = None
        self.remote = EmbyHandler(config['emby'])


class EmbyPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        id = uri.split(':')[-1]

        track_url = self.backend.remote.api_url(
            '/Audio/{}/stream.mp3'.format(id)
        )

        logger.debug('Emby track streaming url: {}'.format(track_url))

        return track_url


class EmbyLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='emby:',
                                          name='Emby')

    def browse(self, uri):
        if uri == self.root_directory.uri:
            music_root = self.backend.remote.get_music_root()
            artists = sorted(
                self.backend.remote.get_directory(music_root)['Items'],
                key=lambda k: k['Name']
            )
            return [
                models.Ref.artist(
                    uri='emby:{}'.format(i['Id']),
                    name=i['Name']
                )
                for i in artists
            ]

        # split uri
        parts = uri.split(':')

        # albums
        if len(parts) == 2:
            id = parts[1]
            albums = sorted(
                self.backend.remote.get_directory(id)['Items'],
                key=lambda k: k['Name']
            )
            return [
                models.Ref.album(
                    uri='emby:{}:{}'.format(id, i['Id']),
                    name=i['Name']
                )
                for i in albums
            ]

        # tracklist
        if len(parts) == 3:
            id = parts[2]
            tracks = sorted(
                self.backend.remote.get_directory(id)['Items']
            )
            return [
                models.Ref.track(
                    uri='emby:{}:{}:{}'.format(id, parts[1], i['Id']),
                    name=i['Name']
                )
                for i in tracks
            ]

        return []

    def lookup(self, uri=None, uris=None):
        logger.debug('Emby lookup: {}'.format(uri or uris))
        if uri:
            parts = uri.split(':')
            logger.debug('Emby lookup: {}'.format(uri))

            if len(parts) == 3:
                tracks = self.backend.remote.get_album_tracks(uri)

            elif len(parts) == 4:
                tracks = [self.backend.remote.get_track(uri)]

            else:
                logger.info('Unknown Emby lookup URI: '.format(uri))
                tracks = []

            return [track for track in tracks if track]

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}


class EmbyHandler(object):
    def __init__(self, config):
        self.hostname = config['hostname']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']

        # create authentication headers
        self.auth_data = self._password_data()
        self.user_id = self._get_user()[0]['Id']
        self.headers = self._create_headers()
        self.token = self._get_token()

        self.headers = self._create_headers(token=self.token)

    def _get_user(self):
        """Return user dict from server or None if there is no user.
        """
        url = self.api_url('/Users/Public')
        r = requests.get(url)
        user = [i for i in r.json() if i['Name'] == self.username]

        return user

    def _get_token(self):
        """Return token for a user.
        """
        url = self.api_url('/Users/AuthenticateByName')
        r = requests.post(url, headers=self.headers, data=self.auth_data)

        return r.json().get('AccessToken')

    def _password_data(self):
        """Returns a dict with username and its encoded password.
        """
        return {
            'username': self.username,
            'password': hashlib.sha1(
                self.password.encode('utf-8')).hexdigest(),
            'passwordMd5': hashlib.md5(
                self.password.encode('utf-8')).hexdigest()
        }

    def _create_headers(self, token=None):
        """Return header dict that is needed to talk to the Emby API.
        """
        headers = {}

        authorization = (
            'MediaBrowser UserId="{user_id}", '
            'Client="other", '
            'Device="mopidy", '
            'DeviceId="mopidy", '
            'Version="0.0.0"'
        ).format(user_id=self.user_id)

        headers['x-emby-authorization'] = authorization

        if token:
            headers['x-mediabrowser-token'] = self.token

        return headers

    def api_url(self, endpoint):
        """Returns a joined url.

        Takes host, port and endpoint and generates a valid emby API url.
        """
        # check if http or https is defined as host and create hostname
        hostname_list = [self.hostname]
        if self.hostname.startswith('http://') or \
                self.hostname.startswith('https://'):
            hostname = ''.join(hostname_list)
        else:
            hostname_list.insert(0, 'http://')
            hostname = ''.join(hostname_list)

        joined = urljoin(
            '{hostname}:{port}'.format(
                hostname=hostname,
                port=self.port
            ),
            endpoint
        )

        scheme, netloc, path, query_string, fragment = urlsplit(joined)
        query_params = parse_qs(query_string)

        query_params['format'] = ['json']
        new_query_string = urlencode(query_params, doseq=True)

        return urlunsplit((scheme, netloc, path, new_query_string, fragment))

    def get_music_root(self):
        url = self.api_url(
            '/Users/{}/Views'.format(self.user_id)
        )

        r = requests.get(url, headers=self.headers)
        data = r.json()
        id = [i['Id'] for i in data['Items'] if i['Name'] == 'Music'][0]

        return id

    def get_directory(self, id):
        return requests.get(
            self.api_url(
                '/Users/{}/Items?ParentId={}&SortOrder=Ascending'.format(
                    self.user_id,
                    id
                )
            ), headers=self.headers
        ).json()

    def get_item(self, id):
        data = requests.get(
            self.api_url(
                '/Users/{}/Items/{}'.format(self.user_id, id)
            ),
            headers=self.headers
        ).json()

        logger.debug('Emby item: {}'.format(data))

        return data

    def create_track(self, uri, track):
        return models.Track(
            uri='{}:{}'.format(uri, track['Id']),
            name=track.get('Name'),
            track_no=track.get('IndexNumber'),
            genre=track.get('Genre'),
            artists=[self.create_artist(track)],
            album=self.create_album(track)
        )

    def create_album(self, track):
        return models.Album(
            name=track.get('Album'),
            artists=[self.create_artist(track)]
        )

    def create_artist(self, track):
        return models.Artist(
            name=track['ArtistItems'][0]['Name'],
            uri='embi:{}'.format(track['ArtistItems'][0]['Id'])
        )

    def get_album_tracks(self, uri):
        id = uri.split(':')[-1]
        data = sorted(self.get_item(id)['Items'], key=lambda k: k['Name'])
        return [self.create_track(uri, i) for i in data]

    def get_track(self, uri):
        id = uri.split(':')[-1]
        track = self.get_item(id)
        return self.create_track(uri, track)
