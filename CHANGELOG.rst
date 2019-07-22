Changelog
=========

v0.5.3
---------------------------------------

- Fix bug with artists/albums not matching if metadata has different capitalization
- Artists that have special characters in their names
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

