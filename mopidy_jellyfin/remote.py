from __future__ import unicode_literals

from mopidy import httpclient, models
from mopidy_jellyfin.utils import cache
import mopidy_jellyfin
from .http import JellyfinHttpClient
from unidecode import unidecode

import logging
from collections import OrderedDict, defaultdict
import sys
if sys.version.startswith('3'):
    from urllib.parse import (
        parse_qs,
        quote,
        urlencode,
        urljoin,
        urlsplit,
        urlunsplit
    )
else:
    from urllib import urlencode
    from urllib2 import quote
    from urlparse import parse_qs, urljoin, urlsplit, urlunsplit

logger = logging.getLogger(__name__)


class JellyfinHandler(object):
    def __init__(self, config):
        self.config = config
        proxy = config.get('proxy')
        jellyfin = config.get('jellyfin')
        if jellyfin:
            self.hostname = jellyfin.get('hostname')
            if jellyfin.get('port', False):
                logger.warn('Specifying port in the config file is '
                            'depreciated. This will be removed in a future '
                            'release. This should be combined with the '
                            'hostname field')
            self.username = jellyfin.get('username')
            self.password = jellyfin.get('password')
            self.libraries = jellyfin.get('libraries')
            # If no libraries are provided, default to 'Music'
            if not self.libraries:
                self.libraries = 'Music'
            self.albumartistsort = jellyfin.get('albumartistsort')
            # If not overridden, default to using Album Artist sort method
            # This _really_ shouldn't be necessary, but it is for reasons
            if self.albumartistsort not in ['False', 'false']:
                self.albumartistsort = True
            else:
                self.albumartistsort = False
            if jellyfin.get('user_id', False):
                logger.warn('Specifying user_id in the config file is '
                            'depreciated. This will be removed in a future '
                            'release')
            cert = None
            client_cert = jellyfin.get('client_cert', None)
            client_key = jellyfin.get('client_key', None)
            if client_cert is not None and client_key is not None:
                cert = (client_cert, client_key)
            self.album_format = jellyfin.get('album_format', False)
            if not self.album_format:
                self.album_format = '{Name}'
        else:
            logger.info('No Jellyfin config found')

        # create authentication headers
        self.auth_data = self._password_data()
        headers = self._create_headers()
        self.http = JellyfinHttpClient(headers, cert, proxy)
        self._login()

    def _save_token(self, token):
        # Save the authentication token where the frontend can also access it
        cache_dir = mopidy_jellyfin.Extension.get_cache_dir(self.config)
        token_file = cache_dir / 'token'

        with open(token_file, 'w') as f:
            f.write(token)

    def _login(self):
        """Return token for a user.
        """
        url = self.api_url('/Users/AuthenticateByName')
        auth_details = self.http.post(
                url, self.auth_data)

        token = auth_details.get('AccessToken')

        if token:
            self.user_id = auth_details.get('User').get('Id')
            headers = {'x-mediabrowser-token': token}
            self.http.session.headers.update(headers)
            self._save_token(token)
        else:
            logger.error('Unable to login to Jellyfin')


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
            'MediaBrowser , '
            'Client="Mopidy", '
            'Device="{device}", '
            'DeviceId="{device_id}", '
            'Version="{version}"'
        ).format(
            device=mopidy_jellyfin.Extension.device_name,
            device_id=mopidy_jellyfin.Extension.device_id,
            version=mopidy_jellyfin.__version__
        )

        headers['x-emby-authorization'] = authorization

        if token:
            headers['x-mediabrowser-token'] = self.token

        return headers

    def api_url(self, endpoint):
        """Returns a joined url.

        Takes host, and endpoint and generates a valid jellyfin API url.
        """
        # check if http or https is defined as host and create hostname
        hostname_list = [self.hostname]
        if self.hostname.startswith('http://') or \
                self.hostname.startswith('https://'):
            hostname = ''.join(hostname_list)
        else:
            hostname_list.insert(0, 'http://')
            hostname = ''.join(hostname_list)

        joined = urljoin(hostname, endpoint)

        scheme, netloc, path, query_string, fragment = urlsplit(joined)
        query_params = parse_qs(query_string)

        query_params['format'] = ['json']
        new_query_string = urlencode(query_params, doseq=True)

        return urlunsplit((scheme, netloc, path, new_query_string, fragment))

    def get_music_root(self):
        url = self.api_url(
            '/Users/{}/Views'.format(self.user_id)
        )

        data = self.http.get(url)

        media_folders = [
            {'Name': library.get('Name'),
             'Id': library.get('Id'),
             'CollectionType': library.get('CollectionType')}
            for library in data.get('Items')
            if library.get('CollectionType') in ['books', 'music']
        ]

        if media_folders:
            logging.debug('Jellyfin: Found libraries')
            return media_folders

        else:
            logging.debug(
                'Jellyfin: All directories found: {}'.format(
                    [i.get('CollectionType')
                     for i in data.get('Items')
                     if 'CollectionType' in i.items()]
                )
            )
            raise Exception('Jellyfin: Cant find music root directory')

    def get_library_roots(self):
        libraries = self.get_music_root()

        return [
            models.Ref.directory(
                uri='jellyfin:directory:{}'.format(i.get('Id')),
                name=i.get('Name')
            ) for i in libraries if i
        ]

    def get_playlists(self):
        url = self.api_url(
            '/Users/{}/Views'.format(self.user_id)
        )

        data = self.http.get(url)

        library_id = [
            library.get('Id') for library in data.get('Items')
            if library.get('Name') == 'Playlists'
        ]

        if library_id:
            library_id = library_id[0]
        else:
            return []

        raw_playlists = self.get_directory(library_id)

        return raw_playlists.get('Items')

    def get_playlist_contents(self, playlist_id):
        url = self.api_url(
            '/Playlists/{}/Items?UserId={}'.format(playlist_id, self.user_id)
        )

        data = self.http.get(url).get('Items')

        return data

    def create_playlist(self, name):
        url = self.api_url('/Playlists')

        payload = {
            'Name': name,
            'UserId': self.user_id,
            'MediaType': 'Audio'
        }

        return self.http.post(url, payload)

    def delete_playlist(self, playlist_id):
        url = self.api_url(
            '/Items/{}?UserId={}'.format(
                playlist_id, self.user_id
            )
        )

        return self.http.delete(url)

    def update_playlist(self, playlist_id, new_ids):
        curr_tracks = self.get_playlist_contents(playlist_id)

        curr_ids = [i.get('PlaylistItemId') for i in curr_tracks]

        del_url = self.api_url(
            'Playlists/{}/Items?UserId={}&EntryIds={}'.format(
                playlist_id, self.user_id, ','.join(str(i) for i in curr_ids)
            )
        )

        self.http.delete(del_url)

        new_url = self.api_url(
            '/Playlists/{}/Items?UserId={}&Ids={}'.format(
                playlist_id, self.user_id, ','.join(new_ids)
            )
        )

        self.http.post(new_url)

    @cache()
    def browse_item(self, item_id):
        contents = self.get_directory(item_id).get('Items')
        ret_value = []

        for item in contents:
            if item.get('Type') == 'Audio':
                ret_value.append(models.Ref.track(
                    uri='jellyfin:track:{}'.format(
                        item.get('Id')
                    ),
                    name=item.get('Name')
                ))
            elif item.get('Type') == 'AudioBook':
                ret_value.append(models.Ref.track(
                    uri='jellyfin:track:{}'.format(
                        item.get('Id')
                    ),
                    name=item.get('Name')
                ))
            elif item.get('Type') == 'MusicAlbum':
                ret_value.append(models.Ref.album(
                    uri='jellyfin:album:{}'.format(item.get('Id')),
                    name=self.format_album(item)
                ))
            elif item.get('Type') == 'Folder':
                ret_value.append(models.Ref.album(
                    uri='jellyfin:album:{}'.format(item.get('Id')),
                    name=item.get('Name')
                ))

        return ret_value

    @cache()
    def get_artists(self):
        artists = []
        libraries = self.get_music_root()

        for library in libraries:

            if library.get('Name') in self.libraries:
                if self.albumartistsort:
                    url = self.api_url(
                        '/Artists/AlbumArtists?ParentId={}&UserId={}'.format(
                            library.get('Id'), self.user_id
                        )
                    )
                else:
                    url = self.api_url(
                        '/Artists?ParentId={}&UserId={}'.format(
                            library.get('Id'), self.user_id
                        )
                    )

                artists += self.http.get(url).get('Items')

        return [
            models.Ref.artist(
                uri='jellyfin:artist:{}'.format(
                    artist.get('Id')
                ),
                name=artist.get('Name')
            )
            for artist in artists
        ]

    @cache()
    def get_albums(self, query):
        raw_artist = [""]
        raw_albums = []

        # Check query for artist name
        if 'artist' in query:
            raw_artist = query.get('artist')
        elif 'albumartist' in query:
            raw_artist = query.get('albumartist')
        else:
            return []

        # URL encode artist string
        artist = quote(raw_artist[0].encode('utf8')).replace('/', '-')
        artist_ref = [models.Artist(name=raw_artist[0])]
        url = self.api_url(
            '/Artists/{}?UserId={}'.format(
                artist, self.user_id)
        )

        # Pull out artist_id
        artist_data = self.http.get(url)
        artist_id = artist_data.get('Id')

        # Get album list
        if self.albumartistsort:
            url = self.api_url(
                '/Items?AlbumArtistIds={}&UserId={}&'
                'IncludeItemTypes=MusicAlbum&Recursive=true'.format(
                    artist_id, self.user_id
                )
            )
        else:
            url = self.api_url(
                '/Items?ArtistIds={}&UserId={}&'
                'IncludeItemTypes=MusicAlbum&Recursive=true'.format(
                    artist_id, self.user_id
                )
            )

        result = self.http.get(url)
        if result:
            raw_albums = result.get('Items')

        albums = [
            models.Album(
                uri='jellyfin:album:{}'.format(item.get('Id')),
                name=item.get('Name'),
                artists=artist_ref
            )
            for item in raw_albums
        ]

        return albums

    @cache()
    def get_directory(self, id):
        """Get directory from Jellyfin API.

        :param id: Directory ID
        :type id: int
        :returns Directory
        :rtype: dict
        """
        return self.http.get(
            self.api_url(
                '/Users/{}/Items?ParentId={}&SortOrder=Ascending'.format(
                    self.user_id, id
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
        data = self.http.get(
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
                track.get('Id')
            ),
            name=track.get('Name'),
            track_no=track.get('IndexNumber'),
            disc_no=track.get('ParentIndexNumber'),
            genre=track.get('Genre'),
            artists=self.create_artists(track),
            album=self.create_album(track),
            length=self.ticks_to_milliseconds(track.get('RunTimeTicks'))
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
                name=artist.get('Name')
            )
            for artist in track.get('ArtistItems')
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

        data = self.http.get(
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

            if item.get('Type') == 'Audio':

                track_artists = [
                    models.Artist(
                        name=artist
                    )
                    for artist in item.get('Artists')
                ]

                tracks.append(
                    models.Track(
                        uri='jellyfin:track:{}'.format(item.get('ItemId')),
                        track_no=item.get('IndexNumber'),
                        name=item.get('Name'),
                        artists=track_artists,
                        album=models.Album(
                            name=item.get('Album'),
                            artists=track_artists
                        )
                    )
                )

            elif item.get('Type') == 'MusicAlbum':
                album_artists = [
                    models.Artist(
                        name=artist
                    )
                    for artist in item.get('Artists')
                ]

                albums.append(
                    models.Album(
                        uri='jellyfin:album:{}'.format(item.get('ItemId')),
                        name=item.get('Name'),
                        artists=album_artists
                    )
                )

            elif item.get('Type') == 'MusicArtist':
                artists.append(
                    models.Artist(
                        uri='jellyfin:artist:{}'.format(item.get('ItemId')),
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
        raw_artist = ''
        artist_ref = []
        raw_albums = []

        # Check query for artist name
        if 'artist' in query:
            raw_artist = query.get('artist')
        elif 'albumartist' in query:
            raw_artist = query.get('albumartist')

        cleaned_artist = unidecode(raw_artist[0]).lower()

        # Use if query has artist name
        if raw_artist:
            # URL encode artist string
            artist = quote(raw_artist[0].encode('utf8')).replace('/', '-')
            artist_ref = [models.Artist(name=raw_artist[0])]
            url = self.api_url(
                '/Artists/{}?UserId={}'.format(
                    artist, self.user_id
                )
            )

            artist_data = self.http.get(url)
            artist_id = artist_data.get('Id')

            # Get album list
            if self.albumartistsort:
                album_url = self.api_url(
                    '/Items?IncludeItemTypes=MusicAlbum&Recursive=true&'
                    'AlbumArtistIds={}&UserId={}&'.format(
                        artist_id, self.user_id
                    )
                )
            else:
                album_url = self.api_url(
                    '/Items?IncludeItemTypes=MusicAlbum&Recursive=true&'
                    'ArtistIds={}&UserId={}&'.format(
                        artist_id, self.user_id
                    )
                )

            album_data = self.http.get(album_url)
            if album_data:
                raw_albums = album_data.get('Items')

            if self.albumartistsort:
                track_url = self.api_url(
                    '/Items?IncludeItemTypes=Audio&Recursive=true&'
                    'AlbumArtistIds={}&UserId={}&'.format(
                        artist_id, self.user_id
                    )
                )
            else:
                track_url = self.api_url(
                    '/Items?IncludeItemTypes=Audio&Recursive=true&'
                    'ArtistIds={}&UserId={}&'.format(
                        artist_id, self.user_id
                    )
                )

            track_data = self.http.get(track_url)
            if track_data:
                # If the query has an album, only match those tracks
                if query.get('album'):
                    tracks = [ models.Track(
                        uri='jellyfin:track:{}'.format(track.get('Id')),
                        track_no=track.get('IndexNumber'),
                        disc_no=track.get('ParentIndexNumber'),
                        name=track.get('Name'),
                        artists=artist_ref,
                        album=models.Album(
                            name=track.get('Album'),
                            artists=artist_ref
                        )
                    ) for track in track_data.get('Items')
                        if track.get('Album') == query.get('album')[0]
                    ]
                # Otherwise return all tracks
                else:
                    tracks = [ models.Track(
                        uri='jellyfin:track:{}'.format(track.get('Id')),
                        track_no=track.get('IndexNumber'),
                        disc_no=track.get('ParentIndexNumber'),
                        name=track.get('Name'),
                        artists=artist_ref,
                        album=models.Album(
                            name=track.get('Album'),
                            artists=artist_ref
                        )
                    ) for track in track_data.get('Items')
                    ]

        # Use if query only has an album name
        elif 'album' in query:
            album_name = query.get('album')[0]
            album = quote(album_name.encode('utf8'))
            if raw_albums:
                album_id = [
                    i.get('Id')
                    for i in raw_albums
                    if i.get('Name') == unidecode(album_name)
                ][0]
            else:
                url = self.api_url(
                    '/Items?IncludeItemTypes=Audio&Recursive=true&'
                    'Albums={}&UserId={}&'.format(
                        album, self.user_id
                    )
                )
                album_data = self.http.get(url).get('Items')

                album_id = album_data[0].get('AlbumId')

                tracks = self.get_search_tracks(artist_ref, album_id)

        return models.SearchResult(
            uri='jellyfin:search',
            tracks=tracks,
            artists=artist_ref,
        )

    @cache()
    def get_search_tracks(self, artist_ref, album_id):
        tracks = []

        url = self.api_url(
            '/Items?IncludeItemTypes=Audio&Recursive=true&'
            'AlbumIds={}&UserId={}&'.format(
                album_id, self.user_id
            )
        )

        result = self.http.get(url)
        if result:
            raw_tracks = result.get('Items')

        if artist_ref:
            # If the artist was in the query,
            # ensure all tracks belong to that artist
            tracks = [
                models.Track(
                    uri='jellyfin:track:{}'.format(item.get('Id')),
                    track_no=item.get('IndexNumber'),
                    disc_no=track.get('ParentIndexNumber'),
                    name=item.get('Name'),
                    artists=artist_ref,
                    album=models.Album(
                        name=item.get('Album'),
                        artists=artist_ref
                    )
                )
                for item in raw_tracks
                if unidecode(artist_ref[0].name.lower()) in (
                    artist.lower() for artist in item.get('Artists'))
            ]
        else:
            # If the query doesn't contain an artist, return all tracks
            tracks = [
                models.Track(
                    uri='jellyfin:track:{}'.format(item.get('Id')),
                    track_no=item.get('IndexNumber'),
                    name=item.get('Name'),
                    artists=artist_ref,
                    album=models.Album(
                        name=item.get('Album'),
                        artists=artist_ref
                    )
                )
                for item in raw_tracks
            ]

        return tracks

    def format_album(self, item):
        # If an error occurs when parsing the custom album format for a given
        # item, fallback to just using the name
        try:
            return self.album_format.format(**item)
        except:
            return item.get('Name')


    def lookup_artist(self, artist_id):
        """Lookup all artist tracks and sort them.

        :param artist_id: Artist ID
        :type artist_id: int
        :returns: List of tracks
        :rtype: list
        """
        if self.albumartistsort:
            url = self.api_url(
                (
                    '/Users/{}/Items?SortOrder=Ascending&AlbumArtistIds={}'
                    '&Recursive=true&IncludeItemTypes=Audio'
                ).format(self.user_id, artist_id)
            )
        else:
            url = self.api_url(
                (
                    '/Users/{}/Items?SortOrder=Ascending&ArtistIds={}'
                    '&Recursive=true&IncludeItemTypes=Audio'
                ).format(self.user_id, artist_id)
            )

        items = self.http.get(url)

        # sort tracks into album keys
        album_dict = defaultdict(list)
        for track in items.get('Items'):
            album_dict[track.get('Album')].append(track)

        # order albums in alphabet
        album_dict = OrderedDict(sorted(album_dict.items()))

        # sort tracks in album dict
        tracks = []
        for album, track_list in album_dict.items():
            track_list.sort(
                key=lambda k: (k.get('IndexNumber', 0), k.get('Name'))
            )

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
        return int(ticks / 10000)

    @staticmethod
    def milliseconds_to_ticks(milliseconds):
        """Converts milliseconds to ticks.

        :param milliseconds: Milliseconds
        :type milliseconds: int
        :returns: Ticks
        :rtype: int
        """
        return milliseconds * 10000
