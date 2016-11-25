from __future__ import unicode_literals

import hashlib
import logging
import time

from urllib import urlencode
from urlparse import parse_qs, urljoin, urlsplit, urlunsplit

from mopidy import backend, httpclient, models

import pykka

import requests

import mopidy_emby


logger = logging.getLogger(__name__)


class EmbyBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['emby']

    def __init__(self, config, audio):
        super(EmbyBackend, self).__init__()

        self.library = EmbyLibraryProvider(backend=self)
        self.playback = EmbyPlaybackProvider(audio=audio, backend=self)
        self.playlist = None
        self.remote = EmbyHandler(config)


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
                self.backend.remote.get_directory(id)['Items'],
                key=lambda k: k['IndexNumber']
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

            elif len(parts) == 4 or len(parts) == 5:
                tracks = [self.backend.remote.get_track(uri)]

            else:
                logger.info('Unknown Emby lookup URI: '.format(uri))
                tracks = []

            return [track for track in tracks if track]

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}


class cache(object):

    def __init__(self, ctl=8, ttl=3600):
        self.cache = {}
        self.ctl = ctl
        self.ttl = ttl
        self._call_count = 1

    def __call__(self, func):
        def _memoized(*args):
            self.func = func
            now = time.time()
            try:
                value, last_update = self.cache[args]
                age = now - last_update
                if self._call_count >= self.ctl or age > self.ttl:
                    self._call_count = 1
                    raise AttributeError

                self._call_count += 1
                return value

            except (KeyError, AttributeError):
                value = self.func(*args)
                self.cache[args] = (value, now)
                return value

            except TypeError:
                return self.func(*args)

        return _memoized


class EmbyHandler(object):
    def __init__(self, config):
        self.hostname = config['emby']['hostname']
        self.port = config['emby']['port']
        self.username = config['emby']['username']
        self.password = config['emby']['password']
        self.proxy = config['proxy']

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

    def _get_session(self):
        proxy = httpclient.format_proxy(self.proxy)
        full_user_agent = httpclient.format_user_agent(
            '/'.join(
                (mopidy_emby.Extension.dist_name, mopidy_emby.__version__)
            )
        )

        session = requests.Session()
        session.proxies.update({'http': proxy, 'https': proxy})
        session.headers.update({'user-agent': full_user_agent})

        return session

    def r_get(self, url):
        counter = 0
        session = self._get_session()
        session.headers.update(self.headers)
        while counter <= 5:
            try:
                r = session.get(url)
                return r.json()
            except Exception as e:
                logger.info(
                    'Emby connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        # if everything goes wrong return a empty dict
        return {}

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

        data = self.r_get(url)
        id = [i['Id'] for i in data['Items'] if i['Name'] == 'Music']

        return id[0]

    @cache()
    def get_directory(self, id):
        return self.r_get(
            self.api_url(
                '/Users/{}/Items?ParentId={}&SortOrder=Ascending'.format(
                    self.user_id,
                    id
                )
            )
        )

    @cache()
    def get_item(self, id):
        data = self.r_get(
            self.api_url(
                '/Users/{}/Items/{}'.format(self.user_id, id)
            )
        )

        logger.debug('Emby item: {}'.format(data))

        return data

    def create_track(self, uri, track):
        # TODO: add more metadata
        return models.Track(
            uri='{}:{}'.format(uri, track['Id']),
            name=track.get('Name'),
            track_no=track.get('IndexNumber'),
            genre=track.get('Genre'),
            artists=self.create_artists(track),
            album=self.create_album(track),
            length=track['RunTimeTicks'] / 10000
        )

    def create_album(self, track):
        return models.Album(
            name=track.get('Album'),
            artists=self.create_artists(track)
        )

    def create_artists(self, track):
        return [
            models.Artist(
                name=artist['Name']
            )
            for artist in track['ArtistItems']
        ]

    @cache()
    def get_album_tracks(self, uri):
        id = uri.split(':')[-1]
        data = sorted(
            self.get_item(id)['Items'], key=lambda k: k['IndexNumber']
        )
        return [self.create_track(uri, i) for i in data]

    @cache()
    def get_track(self, uri):
        id = uri.split(':')[-1]
        track = self.get_item(id)
        return self.create_track(uri, track)
