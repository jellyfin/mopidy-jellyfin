Changelog
=========

v1.0.6
---------------------------------------

- Fix crash when track number is -1

v1.0.5
---------------------------------------

- Place a limit on the json body for now playing api calls
- Properly handle different play command types
- Search for playlist objects instead of a playlists library
- Do no additional quoting for search term

v1.0.4
---------------------------------------

- Added SortBy parameters to solve tracks appearing out of order
- Add ability to authenticate with tokens
- Add date metadata for albums
- Remove trailing slash after reading config file

v1.0.3
---------------------------------------

- Include bitrates for tracks
- Support incremental volume up/down commands
- Add image support
- Attempt to reconnect websocket connection when it fails
- Implement jellyfin:playlists uri for Iris

v1.0.2
---------------------------------------

- Report playback stopped between songs

v1.0.1
---------------------------------------

- Fix search function

v1.0.0
---------------------------------------

- Fallback to 0 if runtimeticks value isn't found
- Sonarcloud cleanup
- Fix bugs in playlist create/delete
- Use favorited tracks as a playlist
- Include more favorites as playlists
- Don't error when trying to modify favorites
- Only show favorite playlists if they have contents

v0.9.3
---------------------------------------

- Refactor and clean up browsing


v0.9.2
---------------------------------------

- More iris fixes
- Remove duplicated code
- Optional flag to show 'watched' status when browsing books

v0.9.1
---------------------------------------

- Add more detailed log messages on connection failure
- Fixes to allow usage with Mopidy-Iris

v0.9.0
---------------------------------------

- Switch away from legacy playback endpoint
- Update websocket receiver for 10.6 changes
- Don't crash if a reporting session isn't found
- Add max bitrate option to enable transcoding

v0.8.1
---------------------------------------

- Fix track genres
- Code quality cleanup
- Follow 301 redirects
- Improve playlist handling

v0.8.0
---------------------------------------

- Add support for baseurl
- Allow for passwordless login
- Report the current tracklist to the server
- Add scheduled playback reporting

v0.7.1
---------------------------------------

- Fix path to cache dir
- Add ability to queue tracks during remote control
- Add ability to resume playback during remote control
- Fix crash when video files are in playlists
- Start at the correct song index during remote control

v0.7.0
---------------------------------------

- Add config option for artist sort method
- Remove need to manually define user_id for hidden users
- Support for servers with a baseurl set
- Remove separate port config option
- Add custom name formats for albums in browse mode
- Add remote control from the Jellyfin Web UI or mobile apps
- Add playback reporting from Mopidy to Jellyfin server


v0.6.0
---------------------------------------

- Add audiobook support
- Doc updates

v0.5.5
---------------------------------------

- Full support for Unicode in artist and albums name
- Python 3 Support
- Fixed bug in album searches being inefficient
- Better caching
- Added getting started development notes
- Instructions for logging in as a hidden user

v0.5.4
---------------------------------------

- Slightly improved error handling
- Optimized playlist logic
- Optimized library population logic

v0.5.3
---------------------------------------

- Fix bug with artists/albums not matching if metadata has different capitalization
- Artists that have special characters in their names load correctly
- All Tracks no longer displays Albums in the wrong field (ncmpcpp only)
- Browsing albums returns correct datatype
- Address Flake8 errors

v0.5.2
---------------------------------------

- Improve artist/album matching in media library
- Fix traceback when browsing an artist or album that contains unicode characters
- Add support to browse "All Tracks" of a given artist

v0.5.1
---------------------------------------

- Doc updates

v0.5.0
---------------------------------------

- Populate media library (Artists, Albums, etc)
- Browse function will show all music type libraries
- Media library is populated based on user's `libraries` setting

v0.4.0
---------------------------------------

- Add playlist support
- Improve client identification to Jellyfin

v0.3.1
---------------------------------------

- Address security vulnerability in dependencies
- Add package to PyPI

v0.3.0
---------------------------------------

- Rebrand to Jellyfin
- Patch auth method to work in Jellyfin
- Add support for multiple audio libraries

v0.2.6
---------------------------------------

- added config option to define a ``user_id``. This is useful if using a hidden user

v0.2.5
---------------------------------------

- debug output for r_get data
- fixed artist lookup

v0.2.4
---------------------------------------

- more testing
- fixed bug in throwing the exception in ``mopidy_emby.remote.EmbyHandler.__get_search``

v0.2.3
---------------------------------------

- Emby streaming is using the static option now. This make seeking possible. This let Emby stream the original file instead of a converted mp3. Thanks to `ebr <https://emby.media/community/index.php?/topic/42501-seek-in-a-stream-from-the-api/>`_.

v0.2.2
---------------------------------------

- ``mopidy_emby.remote.EmbyHandler.r_get`` throws now a exception if cant connect

v0.2.1
---------------------------------------

- Looking for ``CollectionType`` instead of ``Name`` to find music root dir. Fixes `#1 <https://github.com/xsteadfastx/mopidy-emby/issues/1>`_

v0.2.0
---------------------------------------

- Alot of splitting and refactoring

v0.1.3
----------------------------------------

- Throws exception if no music root directory can be found
- SearchResults doesnt use set() no more for killing duplets

v0.1.2
----------------------------------------

- Added searching

v0.1.1
----------------------------------------

- Fixed setup.py requests versioning

v0.1.0
----------------------------------------

- Initial release.

