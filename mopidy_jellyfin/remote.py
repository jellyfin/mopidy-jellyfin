from __future__ import unicode_literals

import hashlib
import logging
import socket
from collections import OrderedDict, defaultdict
from urllib import urlencode
from urllib2 import quote
from urlparse import parse_qs, urljoin, urlsplit, urlunsplit

from mopidy import httpclient, models

import requests

import mopidy_jellyfin
from mopidy_jellyfin.utils import cache

logger = logging.getLogger(__name__)


class JellyfinHandler(object):
    def __init__(self, config):
        self.hostname = config['jellyfin']['hostname']
        self.port = config['jellyfin']['port']
        self.username = config['jellyfin']['username']
        self.password = config['jellyfin']['password']
        self.libraries = config['jellyfin'].get('libraries')
        if not self.libraries:
            self.libraries = 'Music'
        self.proxy = config['proxy']
        self.user_id = config['jellyfin'].get('user_id', False)

        self.cert = None
        client_cert = config['jellyfin'].get('client_cert', None)
        client_key = config['jellyfin'].get('client_key', None)
        if client_cert is not None and client_key is not None:
            self.cert = (client_cert, client_key)

        # create authentication headers
        self.auth_data = self._password_data()
        self.user_id = self.user_id or self._get_user()[0]['Id']
        self.headers = self._create_headers()
        self.token = self._get_token()

        self.headers = self._create_headers(token=self.token)

    def _get_user(self):
        """Return user dict from server or None if there is no user.
        """
        url = self.api_url('/Users/Public')
        r = requests.get(url, cert=self.cert)
        user = [i for i in r.json() if i['Name'] == self.username]

        if user:
            return user
        else:
            raise Exception('No Jellyfin user {} found'.format(self.username))

    def _get_token(self):
        """Return token for a user.
        """
        url = self.api_url('/Users/AuthenticateByName')
        r = requests.post(
                url, headers=self.headers, data=self.auth_data, cert=self.cert)

        return r.json().get('AccessToken')

    def _password_data(self):
        """Returns a dict with username and its encoded password.
        """
        return {
            'username': self.username,
            'Pw': self.password
        }

    def _create_headers(self, token=None):
        """Return header dict that is needed to talk to the Jellyfin API.
        """
        headers = {}

        authorization = (
            'MediaBrowser UserId="{user_id}", '
            'Client="Mopidy", '
            'Device="{name}", '
            'DeviceId="{name}", '
            'Version="{version}"'
        ).format(
            user_id=self.user_id,
            name=socket.gethostname(),
            version=mopidy_jellyfin.__version__
        )

        headers['x-emby-authorization'] = authorization

        if token:
            headers['x-mediabrowser-token'] = self.token

        return headers

    def _get_session(self):
        proxy = httpclient.format_proxy(self.proxy)
        full_user_agent = httpclient.format_user_agent(
            '/'.join(
                (mopidy_jellyfin.Extension.dist_name, mopidy_jellyfin.__version__)
            )
        )

        session = requests.Session()
        session.cert = self.cert
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
                try:
                    rv = r.json()
                except:
                    rv = {}

                logger.debug(str(rv))

                return rv

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def r_post(self, url, *args, **kwargs):
        if args:
            payload = args[0]
        else:
            payload = {}
        counter = 0
        session = self._get_session()
        session.headers.update(self.headers)
        while counter <= 5:

            try:
                r = session.post(url, payload)
                if r.text:
                    rv = r.json()
                else:
                    rv = r.text

                logger.debug(rv)

                return rv

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def r_delete(self, url):
        counter = 0
        session = self._get_session()
        session.headers.update(self.headers)
        while counter <= 5:

            try:
                r = session.delete(url)

                logger.debug(str(r))

                return r

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def api_url(self, endpoint):
        """Returns a joined url.

        Takes host, port and endpoint and generates a valid jellyfin API url.
        """
        # check if http or https is defined as host and create hostname
        hostname_list = [self.hostname]
        if self.hostname.startswith('http://') or \
                self.hostname.startswith('https://'):
            hostname = ''.join(hostname_list)
    def api_url(self, endpoint):
        """Returns a joined url.

        Takes host, port and endpoint and generates a valid jellyfin API url.
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

        media_folders = [
            {'Name': library['Name'],
             'Id':library['Id'],
             'CollectionType':library['CollectionType']}
            for library in data['Items']
            if library['CollectionType'] == 'music'
        ]

        if media_folders:
            logging.debug('Jellyfin: Found libraries')
            return media_folders

        else:
            logging.debug(
                'Jellyfin: All directories found: {}'.format(
                    [i['CollectionType']
                     for i in data['Items']
                     if 'CollectionType' in i.items()]
                )
            )
            raise Exception('Jellyfin: Cant find music root directory')

    def get_library_roots(self):
        libraries = self.get_music_root()

        return [
            models.Ref.directory(
                uri='jellyfin:directory:{}'.format(i['Id']),
                name=i['Name']
            ) for i in libraries if i
        ]

    def get_playlists(self):
        url = self.api_url(
            '/Users/{}/Views'.format(self.user_id)
        )

        data = self.r_get(url)

        library_id = [
            library['Id'] for library in data['Items']
              if library['Name'] == 'Playlists'
        ]

        if library_id:
            library_id = library_id[0]
        else:
            return []


        raw_playlists = self.get_directory(library_id)

        return [
            models.Ref.playlist(
                uri='jellyfin:playlists:{}'.format(i['Id']),
                name='{}'.format(i['Name'])
            ) for i in raw_playlists['Items'] if i
        ]

    def get_playlist_contents(self, playlist_id):
        contents = []
        url = self.api_url(
            '/Playlists/{}/Items?UserId={}'.format(playlist_id, self.user_id)
        )

        data = self.r_get(url)

        if data:
            contents = [
                {
                    'Artist': i['AlbumArtist'],
                    'Title': i['Name'],
                    'Id': i['Id'],
                    'PlaylistItemId': i['PlaylistItemId']
                } for i in data['Items'] if i
            ]

        return contents

    def create_playlist(self, name):
        url = self.api_url('/Playlists')

        payload = {
            'Name': name,
            'UserId': self.user_id,
            'MediaType': 'Audio'
        }

        return self.r_post(url, payload)

    def delete_playlist(self, playlist_id):
        url = self.api_url('/Items/{}?UserId={}'.format(
            playlist_id, self.user_id)
        )

        return self.r_delete(url)

    def update_playlist(self, playlist_id, new_ids):
        curr_tracks = self.get_playlist_contents(playlist_id)

        curr_ids = [i['PlaylistItemId'] for i in curr_tracks]

        del_url = self.api_url(
            'Playlists/{}/Items?UserId={}&EntryIds={}'.format(
                playlist_id, self.user_id, ','.join(str(i) for i in curr_ids))
        )

        clean = self.r_delete(del_url)

        new_url = self.api_url(
            '/Playlists/{}/Items?UserId={}&Ids={}'.format(
                playlist_id, self.user_id, ','.join(new_ids))
        )

        populated = self.r_post(new_url)

    def browse_artists(self, library_id):
        logger.debug('jellyfin: library id - ' + library_id)
        artists = self.get_directory(library_id)['Items']

        return [
            models.Ref.artist(
                uri='jellyfin:artist:{}'.format(i['Id']),
                name=i['Name']
            )
            for i in artists
            if i
        ]

    def browse_albums(self, artist_id):
        logger.debug('jellyfin: artist id - ' + artist_id)
        albums = self.get_directory(artist_id)['Items']

        return [
            models.Ref.artist(
                uri='jellyfin:album:{}'.format(i['Id']),
                name=i['Name']
            )
            for i in albums
            if i
        ]

    def browse_tracks(self, album_id):
        logger.debug('jellyfin: album id - ' + album_id)
        tracks = self.get_directory(album_id)['Items']

        return [
            models.Ref.track(
                uri='jellyfin:track:{}'.format(
                    i['Id']
                ),
                name=i['Name']
            )
            for i in tracks
            if i
        ]

    def get_artists(self):
        artists = []
        libraries = self.get_music_root()

        for library in libraries:

            if library['Name'] in self.libraries:
                url = self.api_url('/Artists?ParentId={}&UserId={}'.format(
                    library['Id'], self.user_id)
                )

                artists += self.r_get(url)['Items']

        return [
            models.Ref.artist(
                uri='jellyfin:artist:{}'.format(
                    artist['Id']
                ),
                name=artist['Name']
            )
            for artist in artists
        ]

    @cache()
    def get_directory(self, id):
        """Get directory from Jellyfin API.

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
        """Get item from Jellyfin API.

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

        logger.debug('Jellyfin item: {}'.format(data))

        return data

    def create_track(self, track):
        """Create track from Jellyfin API track dict.

        :param track: Track from Jellyfin API
        :type track: dict
        :returns: Track
        :rtype: mopidy.models.Track
        """
        # TODO: add more metadata
        return models.Track(
            uri='jellyfin:track:{}'.format(
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

        :param track_id: ID of a Jellyfin track
        :type track_id: int
        :returns: track
        :rtype: mopidy.models.Track
        """
        track = self.get_item(track_id)

        return self.create_track(track)

    def _get_search(self, itemtype, term):
        """Gets search data from Jellyfin API.

        :param itemtype: Type to search for
        :param term: Search term
        :type itemtype: str
        :type term: str
        :returns: List of result dicts
        :rtype: list
        """
        if itemtype == 'any':
            query = 'Audio,MusicAlbum,MusicArtist'
        elif itemtype == 'artist' or itemtype == 'albumartist':
            query = 'MusicArtist'
        elif itemtype == 'album':
            query = 'MusicAlbum'
        elif itemtype == 'track_name':
            query = 'Audio'
        else:
            raise Exception('Jellyfin search: no itemtype {}'.format(itemtype))

        data = self.r_get(
            self.api_url(
                ('/Search/Hints?SearchTerm={}&'
                 'IncludeItemTypes={}').format(
                     quote(term.encode('utf8')),
                     query
                )
            )
        )

        return [i for i in data.get('SearchHints', [])]

    @cache()
    def search(self, query):
        """Search Jellyfin for a term.

        :param query: Search query
        :type query: dict
        :returns: Search results
        :rtype: mopidy.models.SearchResult
        """
        logger.debug('Searching in Jellyfin for {}'.format(query))

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
                        uri='jellyfin:track:{}'.format(item['ItemId']),
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
                        uri='jellyfin:album:{}'.format(item['ItemId']),
                        name=item.get('Name'),
                        artists=album_artists
                    )
                )

            elif item['Type'] == 'MusicArtist':
                artists.append(
                    models.Artist(
                        uri='jellyfin:artist:{}'.format(item['ItemId']),
                        name=item.get('Name')
                    )
                )

        return models.SearchResult(
            uri='jellyfin:search',
            tracks=tracks,
            artists=artists,
            albums=albums
        )

    @cache()
    def exact_search(self, query):
        # Variable prep
        tracks = []
        albums = []
        raw_artist = ''
        artist_ref = []
        raw_albums = []

        # Get artist ID
        if 'artist' in query:
            raw_artist = query.get('artist')
        elif 'albumartist' in query:
            raw_artist = query.get('albumartist')

        # Use if search query has both artist and album
        if 'album' in query and raw_artist:
            artist = quote(raw_artist[0].encode('utf8'))
            artist_ref = [ models.Artist(name = raw_artist[0]) ]
            album_name = query.get('album')[0]
            album = quote(album_name.encode('utf8'))
            if raw_albums:
                album_id = [ i['Id']
                            for i in raw_albums
                            if i['Name'] == album_name
                           ][0]
            else:
                url = self.api_url(
                    '/Items?Albums={}&UserId={}&IncludeItemTypes=Audio&Recursive=true'.format(
                        album, self.user_id)
                )
                album_data = self.r_get(url)['Items']

                album_id = [ i['AlbumId']
                            for i in album_data
                            if raw_artist[0] in i['Artists']
                           ][0]

            tracks = self.get_search_tracks(artist_ref, album_id)

        # Use if query only has artist name
        elif raw_artist:
            artist = quote(raw_artist[0].encode('utf8'))
            artist_ref = [ models.Artist(name = raw_artist[0]) ]
            url = self.api_url(
                '/Artists/{}?UserId={}'.format(
                    artist, self.user_id)
            )

            artist_data = self.r_get(url)
            artist_id = artist_data.get('Id')

            # Get album list
            url = self.api_url(
                '/Items?AlbumArtistIds={}&UserId={}&IncludeItemTypes=MusicAlbum&Recursive=true'.format(
                    artist_id, self.user_id)
            )

            result = self.r_get(url)
            if result:
                raw_albums = result['Items']

            for album in raw_albums:
                tracks += self.get_search_tracks(artist_ref, album['Id'])

            albums = [
                models.Album(
                    uri='jellyfin:album:{}'.format(item.get('Id')),
                    name=item.get('Name'),
                    artists=artist_ref
                )
                for item in raw_albums
            ]

        # Use if query only has an album name
        elif 'album' in query:
            album_name = query.get('album')[0]
            album = quote(album_name.encode('utf8'))
            if raw_albums:
                album_id = [ i['Id']
                            for i in raw_albums
                            if i['Name'] == album_name
                           ][0]
            else:
                url = self.api_url(
                    '/Items?Albums={}&UserId={}&IncludeItemTypes=Audio&Recursive=true'.format(
                        album, self.user_id)
                )
                album_data = self.r_get(url)['Items']

                album_id = album_data[0]['AlbumId']

                tracks = self.get_search_tracks(artist_ref, album_id)

        return models.SearchResult(
            uri='jellyfin:search',
            tracks=tracks,
            artists=artist_ref,
            albums=albums
        )

    def get_search_tracks(self, artist_ref, album_id):
        tracks = []

        if artist_ref:
            url = self.api_url(
                '/Items?AlbumIds={}&UserId={}&IncludeItemTypes=Audio&Recursive=true'.format(
                    album_id, self.user_id)
            )

            result = self.r_get(url)
            if result:
                raw_tracks = result['Items']

            tracks = [
                models.Track(
                    uri='jellyfin:track:{}'.format(item['Id']),
                    track_no=item.get('IndexNumber'),
                    name=item.get('Name'),
                    artists=artist_ref,
                    album=models.Album(
                        name=item.get('Album'),
                        artists=artist_ref
                    )
                )
                for item in raw_tracks
                if artist_ref[0].name in item.get('Artists')
            ]

        return tracks

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
            track_list.sort(key=lambda k: (k.get('IndexNumber', 0),k.get('Name')))

            # add tracks to list
            tracks.extend(track_list)

        return [self.create_track(i) for i in tracks]

    @staticmethod
    def ticks_to_milliseconds(ticks):
        """Converts Jellyfin track length ticks to milliseconds.

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
