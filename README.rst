****************************
Mopidy-Jellyfin
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Jellyfin.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Jellyfin/
    :alt: Latest PyPI version


Mopidy extension for playing audio files from Jellyfin

Notes:

- Currently only supports the "Music" media type
- Tested using `ncmpcpp <https://rybczak.net/ncmpcpp/>`_ and `M.A.L.P. <https://play.google.com/store/apps/details?id=org.gateshipone.malp>`_
- MPDroid on Android does not work properly


Installation
============

Install by running::

    pip2 install Mopidy-Jellyfin

Note that mopidy is still limited to python 2

Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Jellyfin to your Mopidy configuration file::

    [jellyfin]
    hostname = Jellyfin server hostname
    port = Jellyfin server port
    username = username
    password = password
    libraries = Library1, Library2 (Optional: will default to "Music" if left undefined)

The `libraries` option determines what is populated into Mopidy's internal library (view by Artists/Album/etc).  Using the file browser will show all libraries in the Jellyfin server that have a 'music' type.

It's also possible to add a users id with ``user_id = 0``.


Project resources
=================

- `Source code <https://github.com/mcarlton00/mopidy-jellyfin>`_
- `Issue tracker <https://github.com/mcarlton00/mopidy-jellyfin/issues>`_


Credits
=======

- Current maintainer: `Matt Carlton <https://github.com/mcarlton00>`_
- Original author: `Marvin Steadfast <https://github.com/xsteadfastx>`_
- `Contributors <https://github.com/mcarlton00/mopidy-jellyfin/graphs/contributors>`_


Changelog
=========

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
