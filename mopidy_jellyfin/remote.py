from __future__ import unicode_literals

from mopidy import httpclient, models
from mopidy_jellyfin.utils import cache
import mopidy_jellyfin
from .http import JellyfinHttpClient
from unidecode import unidecode
import os
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
        self.hostname = jellyfin.get('hostname')
        self.username = jellyfin.get('username')
        self.password = jellyfin.get('password', '')
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
        max_bitrate = jellyfin.get('max_bitrate')
        if max_bitrate:
            self.max_bitrate = str(max_bitrate * 1024)
        else:
            self.max_bitrate = '140000000'
        self.watched_status = jellyfin.get('watched_status')
        cert = None
        client_cert = jellyfin.get('client_cert', None)
        client_key = jellyfin.get('client_key', None)
        if client_cert is not None and client_key is not None:
            cert = (client_cert, client_key)
        self.album_format = jellyfin.get('album_format', False)
        if not self.album_format:
            self.album_format = '{Name}'

        # create authentication headers
        self.auth_data = self._auth_payload()
        headers = self._create_headers()
        self.http = JellyfinHttpClient(headers, cert, proxy)
        response_url = self.http.check_redirect(self.hostname)
        if self.hostname != response_url:
            self.hostname = response_url
        self._login()

    def _save_token(self, token):
        # Save the authentication token where the frontend can also access it
        cache_dir = mopidy_jellyfin.Extension.get_cache_dir(self.config)
        token_file = os.path.join(cache_dir, 'token')

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
            self.token = token
        else:
            logger.error('Unable to login to Jellyfin')


    def _auth_payload(self):
        """Returns a dict with username and password.
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

    def api_url(self, endpoint, url_params={}):
        """Returns a joined url.

        Takes host, and endpoint and generates a valid jellyfin API url.
        """

        scheme, netloc, path, query_string, fragment = urlsplit(self.hostname)
        query_params = parse_qs(query_string)
        path = path + endpoint

        query_params['format'] = 'json'
        query_params.update(url_params)
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
        url_params = { 'UserId': self.user_id }
        url = self.api_url('/Playlists/{}/Items'.format(playlist_id), url_params)

        data = self.http.get(url).get('Items', [])

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
        url_params = { 'UserId': self.user_id }
        url = self.api_url('/Items/{}'.format(playlist_id), url_params)

        result = self.http.delete(url)
        return result.ok

    def update_playlist(self, playlist_id, new_ids):
        curr_tracks = self.get_playlist_contents(playlist_id)

        curr_length = len(curr_tracks)
        new_length = len(new_ids)

        if curr_length == new_length:
            # If the playlist is the same length, assume a track has moved
            self.move_playlist_items(playlist_id, curr_tracks, new_ids)
        elif curr_length > new_length:
            # If the new playlist is shorter than the old, delete tracks
            self.delete_from_playlist(playlist_id, curr_tracks, new_ids)
        elif curr_length < new_length:
            # If the new playlist is longer than the old, add new tracks
            self.add_to_playlist(playlist_id, curr_tracks, new_ids)

    def move_playlist_items(self, playlist_id, curr_tracks, new_ids):
        # Loop through the current and new list, finding the moved track
        for index,item in enumerate(curr_tracks, 0):
            if item['Id'] != new_ids[index]:
                new_index = new_ids.index(item['Id'])
                # If an item has only moved down 1 slot, it was likely caused
                # by another track being moved above it
                if new_index - index != 1:
                    break

        # Playlists have their own unique item IDs
        item_id = item['PlaylistItemId']

        url = self.api_url(f'/Playlists/{playlist_id}/Items/{item_id}/Move/{new_index}')
        self.http.post(url)

    def delete_from_playlist(self, playlist_id, curr_tracks, new_ids):
        curr_ids = [ track['Id'] for track in curr_tracks ]

        # Find items that are in the old playlist but missing from the new one
        del_items = list(set(curr_ids) - set(new_ids))

        # Get the PlaylistItemId of each track to be deleted
        del_ids = [ track['PlaylistItemId'] for track in curr_tracks if track['Id'] in del_items ]

        url_params = {
            'UserId': self.user_id,
            'EntryIds': ','.join(del_ids)
        }
        del_url = self.api_url(f'Playlists/{playlist_id}/Items', url_params)
        self.http.delete(del_url)

    def add_to_playlist(self, playlist_id, curr_tracks, new_ids):
        curr_ids = [ track['Id'] for track in curr_tracks ]

        # Find items in the new playlist that are missing from the old one
        add_ids = list(set(new_ids) - set(curr_ids))

        url_params = {
            'UserId': self.user_id,
            'Ids': ','.join(add_ids)
        }
        new_url = self.api_url(f'/Playlists/{playlist_id}/Items', url_params)
        self.http.post(new_url)

    def get_favorites(self):
        '''
        Pulls a list of favorite audio related content from the server and
        build playlists from it
        '''

        # Types of playlists to build
        playlists = {
            'All': [],
            'Tracks': [],
            'Albums': [],
            'Artists': []
        }

        url_params = {
            'Recursive': 'true',
            'Filters': 'IsFavorite',
        }

        fav_items_url = self.api_url(f'/Users/{self.user_id}/Items', url_params)
        fav_items = self.http.get(fav_items_url).get('Items', [])

        for item in fav_items:
            item_type = item.get('Type')
            if item_type == 'Audio':
                playlists['Tracks'].append(self.create_track(item))
            elif item_type == 'MusicAlbum':
                # Get tracks from the favorited album
                tracks = self.get_directory(item.get('Id')).get('Items', [])
                playlists['Albums'].extend([
                    self.create_track(track) for track in tracks])

        # User ID needed for the artists query
        url_params['UserId'] = self.user_id

        # Artists aren't available in the previous call and have to be separate
        fav_artists_url = self.api_url(f'/Artists', url_params)
        fav_artists = self.http.get(fav_artists_url).get('Items', [])

        for artist in fav_artists:
            # Get tracks from the favorited artist
            artist_id = artist.get('Id')
            playlists['Artists'].extend(self.lookup_artist(artist_id))

        # 'All' should include the other 3 lists combined
        playlists['All'].extend(playlists['Tracks'])
        playlists['All'].extend(playlists['Albums'])
        playlists['All'].extend(playlists['Artists'])

        return playlists


    @cache()
    def browse_item(self, item_id):
        item = self.get_item(item_id)
        if item.get('CollectionType', '') == 'music':
            # Pull all artists for this library
            artists = self.get_library_artists(item_id)
            ret_value = [self.get_artist_as_ref(artist) for artist in artists]
        elif item.get('Type', '') == 'MusicArtist':
            # Pull list of albums for a given artist
            ret_value = self.get_artist_contents(item_id)
        else:
            # Browse the directory tree
            contents = self.get_directory(item_id).get('Items')
            ret_value = []

            # Create an entry for each item depending on it's type
            for item in contents:
                if item.get('Type') in ('Audio', 'AudioBook'):
                    # Create tracks
                    ret_value.append(self.get_track_as_ref(item))
                elif item.get('Type') == 'MusicArtist':
                    # Create artists (probably never used)
                    ret_value.append(self.get_artist_as_ref(item))
                elif item.get('Type') in ('MusicAlbum', 'Folder'):
                    # Create browsable folders
                    ret_value.append(self.get_album_as_ref(item))

        return ret_value

    @cache()
    def get_all_artists(self):
        # Get a list of all artists in the server.  Used for mopidy-iris
        artists = []
        libraries = self.get_music_root()

        for library in libraries:

            if library.get('Name') in self.libraries:
                library_id = library.get('Id')
                artists += self.get_library_artists(library_id)

        return artists

    @cache()
    def get_artist_contents(self, artist_id):
        # Get a list of albums for the given artist
        contents = []
        ret_val = []

        # Get album list
        url_params = {
            'UserId': self.user_id,
            'IncludeItemTypes': 'MusicAlbum',
            'Recursive': 'true'
        }
        if self.albumartistsort:
            url_params['AlbumArtistIds'] = artist_id
        else:
            url_params['ArtistIds'] = artist_id

        url = self.api_url('/Items', url_params)
        result = self.http.get(url)
        if result:
            contents = result.get('Items')

        ret_val = [self.get_album_as_ref(album) for album in contents]

        return ret_val

    @cache()
    def get_library_artists(self, library_id):
        # Get a list of all artists in the given library
        url_params = {
            'ParentId': library_id,
            'UserId': self.user_id
        }
        if self.albumartistsort:
            url = self.api_url('/Artists/AlbumArtists', url_params)
        else:
            url = self.api_url('/Artists', url_params)

        artists = self.http.get(url).get('Items')

        return artists

    @cache()
    def get_artist_as_ref(self, artist):
        # Convert artist into mopidy object
        artist_ref = models.Ref.artist(
            uri='jellyfin:artist:{}'.format(
                artist.get('Id')
            ),
            name=artist.get('Name')
        )

        return artist_ref

    @cache()
    def get_album_as_ref(self, album):
        # Convert album into mopidy object
        return models.Ref.album(
            uri='jellyfin:album:{}'.format(
                album.get('Id')
            ),
            name=album.get('Name')
        )

    def get_track_as_ref(self, track):
        # Convert track into mopidy object
        return models.Ref.track(
            uri='jellyfin:track:{}'.format(
                track.get('Id')
            ),
            name=track.get('Name')
        )

    @cache()
    def get_albums(self, query):
        # Check query for artist name
        if 'artist' in query:
            raw_artist = query.get('artist')
        elif 'albumartist' in query:
            raw_artist = query.get('albumartist')
        else:
            return []

        # URL encode artist string
        artist = quote(raw_artist[0].encode('utf8')).replace('/', '-')
        url_params= {
            'UserId': self.user_id
        }
        url = self.api_url('/Artists/{}'.format(artist), url_params)

        # Pull out artist_id
        artist_data = self.http.get(url)
        artist_id = artist_data.get('Id')

        url_params = {
            'UserId': self.user_id,
            'IncludeItemTypes': 'MusicAlbum',
            'Recursive': 'true'
        }

        # Get album list
        if self.albumartistsort:
            url_params['AlbumArtistIds'] = artist_id
        else:
            url_params['ArtistIds'] = artist_id

        url = self.api_url('/Items', url_params)
        result = self.http.get(url)
        if result:
            albums = result.get('Items')

        return albums

    @cache()
    def get_all_albums(self):
        # Get a list of all albums in the library.  Used for mopidy-iris
        url_params = {
            'UserId': self.user_id,
            'IncludeItemTypes': 'MusicAlbum',
            'Recursive': 'true'
        }

        url = self.api_url('/Items', url_params)
        albums = self.http.get(url).get('Items')

        return albums

    @cache()
    def get_directory(self, id):
        """Get directory from Jellyfin API.

        :param id: Directory ID
        :type id: int
        :returns Directory
        :rtype: dict
        """
        url_params= {
            'ParentId': id,
            'SortOrder': 'Ascending'
        }
        url = self.api_url('/Users/{}/Items'.format(self.user_id), url_params)
        return self.http.get(url)

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
        name = track.get('Name')
        if self.watched_status and track.get('Type') == 'AudioBook':
            if track['UserData'].get('PlayCount'):
                name = f'[X] - {name}'
            else:
                name = f'[] - {name}'

        return models.Track(
            uri='jellyfin:track:{}'.format(track.get('Id')),
            name=name,
            track_no=track.get('IndexNumber', 0),
            disc_no=track.get('ParentIndexNumber'),
            genre=','.join(track.get('Genres', [])),
            artists=self.create_artists(track),
            album=self.create_album(track),
            length=self.ticks_to_milliseconds(track.get('RunTimeTicks', 0))
        )

    def create_album(self, item):
        """Create album object from Jellyfin item.

        :param track: item
        :type track: dict
        :returns: Album
        :rtype: mopidy.models.Album
        """
        item_type = item.get('Type')
        if item_type == 'Audio':
            return models.Album(
                name=item.get('Album'),
                artists=self.create_artists(item),
                uri=f'jellyfin:album:{item.get("AlbumId")}'
            )
        elif item_type == 'MusicAlbum':
            return models.Album(
                name=item.get('Name'),
                artists=self.create_artists(item),
                uri=f'jellyfin:album:{item.get("Id")}'
            )

    def create_artists(self, item={}, name=None):
        """Create artist object from jellyfin item.

        :param track: item
        :type track: dict
        :param name: Name
        :type name: str
        :returns: List of artists
        :rtype: list of mopidy.models.Artist
        """
        item_type = item.get('Type', '')
        if item_type == 'MusicArtist':
            # Artists have a slightly different structure
            return [
                models.Artist(name=item.get('Name'),
                              uri=f'jellyfin:artist:{item.get("Id")}')
            ]
        elif item_type:
            # For tracks and albums
            return [
                models.Artist(name=artist, uri=f'jellyfin:artist:{item.get("Id")}')
                for artist in item.get('Artists', [])
            ]
        else:
            # In case we only get a name
            return [ models.Artist(name=name) ]

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
            search_query = 'Audio,MusicAlbum,MusicArtist'
        elif itemtype == 'artist' or itemtype == 'albumartist':
            search_query = 'MusicArtist'
        elif itemtype == 'album':
            search_query = 'MusicAlbum'
        elif itemtype == 'track_name':
            search_query = 'Audio'
        else:
            raise Exception('Jellyfin search: no itemtype {}'.format(itemtype))

        url_params = {
            'SearchTerm': quote(term.encode('utf-8')),
            'IncludeItemTypes': search_query
        }

        url = self.api_url('/Search/Hints', url_params)
        data = self.http.get(url)

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
                tracks.append(self.create_track(item))

            elif item.get('Type') == 'MusicAlbum':
                albums.append(self.create_album(item))

            elif item.get('Type') == 'MusicArtist':
                artists.extend(self.create_artists(item))

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
        albums = []

        # Check query for artist name
        if 'artist' in query:
            raw_artist = query.get('artist')
        elif 'albumartist' in query:
            raw_artist = query.get('albumartist')

        # Use if query has artist name
        if raw_artist:
            # URL encode artist string
            artist = quote(raw_artist[0].encode('utf8')).replace('/', '-')
            artist_ref = self.create_artists(name=raw_artist[0])
            url_params = { 'UserId': self.user_id }
            url = self.api_url('/Artists/{}'.format(artist), url_params)

            artist_data = self.http.get(url)
            artist_id = artist_data.get('Id')

            url_params = {
                'IncludeItemTypes': 'MusicAlbum',
                'Recursive': 'true',
                'UserId': self.user_id
            }

            # Get album list
            if self.albumartistsort:
                url_params['AlbumArtistIds'] = artist_id
            else:
                url_params['ArtistIds'] = artist_id

            album_url = self.api_url('/Items', url_params)
            album_data = self.http.get(album_url)
            if album_data:
                contents = album_data.get('Items')
                for item in contents:
                    if item.get('Type') == 'MusicAlbum':
                        album_obj = models.Album(
                            name=item.get('Name'),
                            artists=self.create_artists(item),
                            uri='jellyfin:album:{}'.format(item.get('Id'))
                        )
                        if album_obj not in albums:
                            albums.append(album_obj)

            # Get artist tracks
            url_params['IncludeItemTypes'] = 'Audio'
            track_url = self.api_url('/Items', url_params)
            track_data = self.http.get(track_url)
            if track_data:
                # If the query has an album, only match those tracks
                if query.get('album'):
                    tracks = [
                        self.create_track(track)
                        for track in track_data.get('Items')
                        if track.get('Album') == query.get('album')[0]
                    ]
                # Otherwise return all tracks
                else:
                    tracks = [
                        self.create_track(track)
                        for track in track_data.get('Items')
                    ]

        # Use if query only has an album name
        elif 'album' in query:
            album_name = query.get('album')[0]
            url_params = {
                'IncludeItemTypes': 'MusicAlbum',
                'IncludeMedia': 'true',
                'Recursive': 'true',
                'searchTerm': album_name
            }
            url = self.api_url('/Users/{}/Items'.format(self.user_id), url_params)
            album_data = self.http.get(url).get('Items')
            tracks = []
            # This can lead to false matches, but all we have at this point
            # is an album name to match against.  Options are limited
            for album in album_data:
                if album.get('Name') == album_name:
                    album_obj = models.Album(
                        name=album.get('Name'),
                        artists=self.create_artists(album),
                        uri='jellyfin:album:{}'.format(album.get('Id'))
                    )
                    if album_obj not in albums:
                        albums.append(album_obj)
                    raw_tracks = self.get_directory(album.get('Id'))
                    tracks += [self.create_track(track)
                               for track in raw_tracks.get('Items', [])]

        return models.SearchResult(
            uri='jellyfin:search',
            tracks=tracks,
            albums=albums,
            artists=artist_ref,
        )

    @cache()
    def get_search_tracks(self, artist_ref, album_id):
        tracks = []

        url_params = {
            'IncludeItemTypes': 'Audio',
            'Recursive': 'true',
            'AlbumIds': album_id,
            'UserId': self.user_id
        }
        url = self.api_url('/Items', url_params)

        result = self.http.get(url)
        if result:
            raw_tracks = result.get('Items')

        if artist_ref:
            # If the artist was in the query,
            # ensure all tracks belong to that artist
            tracks = [
                self.create_track(track)
                for track in raw_tracks
                if unidecode(artist_ref[0].name.lower()) in (
                    artist.lower() for artist in track.get('Artists'))
            ]
        else:
            # If the query doesn't contain an artist, return all tracks
            tracks = [
                self.create_track(track)
                for track in raw_tracks
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
        url_params = {
            'SortOrder': 'Ascending',
            'Recursive': 'true',
            'IncludeItemTypes': 'Audio'
        }
        if self.albumartistsort:
            url_params['AlbumArtistIds'] = artist_id
        else:
            url_params['ArtistIds'] = artist_id

        url = self.api_url('/Users/{}/Items'.format(self.user_id), url_params)
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
