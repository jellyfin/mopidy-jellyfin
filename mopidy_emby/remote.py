from __future__ import unicode_literals

import hashlib

import logging

from collections import OrderedDict, defaultdict

from urllib import urlencode
from urllib2 import quote
from urlparse import parse_qs, urljoin, urlsplit, urlunsplit

from mopidy import httpclient, models

import requests

import mopidy_emby

from mopidy_emby.utils import cache


logger = logging.getLogger(__name__)


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

        if user:
            return user
        else:
            raise Exception('No Emby user {} found'.format(self.username))

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
                rv = r.json()

                logger.debug(str(rv))

                return rv

            except Exception as e:
                logger.info(
                    'Emby connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Emby API')

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

        id = [i['Id']
              for i in data['Items']
              if 'CollectionType' in i.keys()
              if i['CollectionType'] == 'music']

        if id:
            logging.debug(
                'Emby: Found music root dir with ID: {}'.format(id[0])
            )
            return id[0]

        else:
            logging.debug(
                'Emby: All directories found: {}'.format(
                    [i['CollectionType']
                     for i in data['Items']
                     if 'CollectionType' in i.items()]
                )
            )
            raise Exception('Emby: Cant find music root directory')

    def get_artists(self):
        music_root = self.get_music_root()
        artists = sorted(
            self.get_directory(music_root)['Items'],
            key=lambda k: k['Name']
        )

        return [
            models.Ref.artist(
                uri='emby:artist:{}'.format(i['Id']),
                name=i['Name']
            )
            for i in artists
            if i
        ]

    def get_albums(self, artist_id):
        albums = sorted(
            self.get_directory(artist_id)['Items'],
            key=lambda k: k['Name']
        )
        return [
            models.Ref.album(
                uri='emby:album:{}'.format(i['Id']),
                name=i['Name']
            )
            for i in albums
            if i
        ]

    def get_tracks(self, album_id):
        tracks = sorted(
            self.get_directory(album_id)['Items'],
            key=lambda k: k['IndexNumber']
        )

        return [
            models.Ref.track(
                uri='emby:track:{}'.format(
                    i['Id']
                ),
                name=i['Name']
            )
            for i in tracks
            if i
        ]

    @cache()
    def get_directory(self, id):
        """Get directory from Emby API.

        :param id: Directory ID
        :type id: int
        :returns Directory
        :rtype: dict
        """
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
        """Get item from Emby API.

        :param id: Item ID
        :type id: int
        :returns: Item
        :rtype: dict
        """
        data = self.r_get(
            self.api_url(
                '/Users/{}/Items/{}'.format(self.user_id, id)
            )
        )

        logger.debug('Emby item: {}'.format(data))

        return data

    def create_track(self, track):
        """Create track from Emby API track dict.

        :param track: Track from Emby API
        :type track: dict
        :returns: Track
        :rtype: mopidy.models.Track
        """
        # TODO: add more metadata
        return models.Track(
            uri='emby:track:{}'.format(
                track['Id']
            ),
            name=track.get('Name'),
            track_no=track.get('IndexNumber'),
            genre=track.get('Genre'),
            artists=self.create_artists(track),
            album=self.create_album(track),
            length=self.ticks_to_milliseconds(track['RunTimeTicks'])
        )

    def create_album(self, track):
        """Create album object from track.

        :param track: Track
        :type track: dict
        :returns: Album
        :rtype: mopidy.models.Album
        """
        return models.Album(
            name=track.get('Album'),
            artists=self.create_artists(track)
        )

    def create_artists(self, track):
        """Create artist object from track.

        :param track: Track
        :type track: dict
        :returns: List of artists
        :rtype: list of mopidy.models.Artist
        """
        return [
            models.Artist(
                name=artist['Name']
            )
            for artist in track['ArtistItems']
        ]

    @cache()
    def get_track(self, track_id):
        """Get track.

        :param track_id: ID of a Emby track
        :type track_id: int
        :returns: track
        :rtype: mopidy.models.Track
        """
        track = self.get_item(track_id)

        return self.create_track(track)

    def _get_search(self, itemtype, term):
        """Gets search data from Emby API.

        :param itemtype: Type to search for
        :param term: Search term
        :type itemtype: str
        :type term: str
        :returns: List of result dicts
        :rtype: list
        """
        if itemtype == 'any':
            query = 'Audio,MusicAlbum,MusicArtist'
        elif itemtype == 'artist':
            query = 'MusicArtist'
        elif itemtype == 'album':
            query = 'MusicAlbum'
        elif itemtype == 'track_name':
            query = 'Audio'
        else:
            raise Exception('Emby search: no itemtype {}'.format(itemtype))

        data = self.r_get(
            self.api_url(
                ('/Search/Hints?SearchTerm={}&'
                 'IncludeItemTypes={}').format(
                     quote(term),
                     query
                )
            )
        )

        return [i for i in data.get('SearchHints', [])]

    @cache()
    def search(self, query):
        """Search Emby for a term.

        :param query: Search query
        :type query: dict
        :returns: Search results
        :rtype: mopidy.models.SearchResult
        """
        logger.debug('Searching in Emby for {}'.format(query))

        # something to store the results in
        data = []
        tracks = []
        albums = []
        artists = []

        for itemtype, term in query.items():

            for item in term:

                data.extend(
                    self._get_search(itemtype, item)
                )

        # walk through all items and create stuff
        for item in data:

            if item['Type'] == 'Audio':

                track_artists = [
                    models.Artist(
                        name=artist
                    )
                    for artist in item['Artists']
                ]

                tracks.append(
                    models.Track(
                        uri='emby:track:{}'.format(item['ItemId']),
                        track_no=item.get('IndexNumber'),
                        name=item.get('Name'),
                        artists=track_artists,
                        album=models.Album(
                            name=item.get('Album'),
                            artists=track_artists
                        )
                    )
                )

            elif item['Type'] == 'MusicAlbum':
                album_artists = [
                    models.Artist(
                        name=artist
                    )
                    for artist in item['Artists']
                ]

                albums.append(
                    models.Album(
                        uri='emby:album:{}'.format(item['ItemId']),
                        name=item.get('Name'),
                        artists=album_artists
                    )
                )

            elif item['Type'] == 'MusicArtist':
                artists.append(
                    models.Artist(
                        uri='emby:artist:{}'.format(item['ItemId']),
                        name=item.get('Name')
                    )
                )

        return models.SearchResult(
            uri='emby:search',
            tracks=tracks,
            artists=artists,
            albums=albums
        )

    def lookup_artist(self, artist_id):
        """Lookup all artist tracks and sort them.

        :param artist_id: Artist ID
        :type artist_id: int
        :returns: List of tracks
        :rtype: list
        """
        url = self.api_url(
            (
                '/Users/{}/Items?SortOrder=Ascending&ArtistIds={}'
                '&Recursive=true&IncludeItemTypes=Audio'
            ).format(self.user_id, artist_id)
        )

        items = self.r_get(url)

        # sort tracks into album keys
        album_dict = defaultdict(list)
        for track in items['Items']:
            album_dict[track['Album']].append(track)

        # order albums in alphabet
        album_dict = OrderedDict(sorted(album_dict.items()))

        # sort tracks in album dict
        tracks = []
        for album, track_list in album_dict.items():
            track_list.sort(key=lambda k: k['IndexNumber'])

            # add tracks to list
            tracks.extend(track_list)

        return [self.create_track(i) for i in tracks]

    @staticmethod
    def ticks_to_milliseconds(ticks):
        """Converts Emby track length ticks to milliseconds.

        :param ticks: Ticks
        :type ticks: int
        :returns: Milliseconds
        :rtype: int
        """
        return ticks / 10000

    @staticmethod
    def milliseconds_to_ticks(milliseconds):
        """Converts milliseconds to ticks.

        :param milliseconds: Milliseconds
        :type milliseconds: int
        :returns: Ticks
        :rtype: int
        """
        return milliseconds * 10000
