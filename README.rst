****************************
Mopidy-Jellyfin
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Jellyfin.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Jellyfin/
    :alt: Latest PyPI version


Mopidy extension for playing audio files from Jellyfin

Notes:

- Supports both "Music" and "Book" media types
- Tested using `ncmpcpp <https://rybczak.net/ncmpcpp/>`_, `M.A.L.P. <https://play.google.com/store/apps/details?id=org.gateshipone.malp>`_, and various mopidy `web frontends <https://mopidy.com/ext/>`_.
    - When using ncmpcpp, it's recommended to set ``mpd_connection_timeout = 30``, particularly if browsing folders that have a large number of items inside them
    - There is some inconsistency in M.A.L.P. where you may have to go to the menu and select 'Show All Tracks' for the library to populate properly
- MPDroid on Android does not work properly


Installation
============

Install by running::

    pip install Mopidy-Jellyfin

Mopidy-Jellyfin has officially moved to Python 3 with the release of `Mopidy 3.0 <https://mopidy.com/blog/2019/12/22/mopidy-3.0/>`_.  All future updates will target this newer version.


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Jellyfin to your Mopidy configuration file::

    [jellyfin]
    hostname = Jellyfin server hostname
    username = username
    password = password
    libraries = Library1, Library2 (Optional: will default to "Music" if left undefined)
    albumartistsort = False (Optional: will default to True if left undefined)
    album_format = {ProductionYear} - {Name} (Optional: will default to "{Name}" if left undefined)
    max_bitrate = number

* ``libraries`` determines what is populated into Mopidy's internal library (view by Artists/Album/etc).  Using the file browser will show all libraries in the Jellyfin server that have a 'music' type.

* ``albumartistsort`` changes whether the media library populates based on "Artist" or "Album Artist" metadata

* ``album_format`` can be used to change the display format of music albums when using the file browser view.  Currently the only really usable fields are ProductionYear and Name

  ``max_bitrate`` is used to trigger transcoding if a file is over a given bitrate (in kbps)


Development
===========

1. Install mopidy to your host system, preferably using the native package manager.  This handles all of the required dependencies.

2. Clone the repo to your local workstation

   ``$ git clone git@github.com:jellyfin/mopidy-jellyfin.git && cd mopidy-jellyfin``

2. Set up a virtualenv.  We need to include system packages since some things don't behave well inside of a virtualenv (such as ``PyGObject`` or interacting with pulseaudio).  Note that with the release of Mopidy 3.0 only Python 3.7 or newer is supported.

   ``$ python -m venv env --system-site-packages``

3. Install mopidy-jellyfin to the virtualenv.

   ``$ env/bin/python setup.py develop``

4. Do your thing.

   Mopidy can be launched from the virtualenv with ``env/bin/mopidy``


Project resources
=================

- `Source code <https://github.com/jellyfin/mopidy-jellyfin>`_
- `Issue tracker <https://github.com/jellyfin/mopidy-jellyfin/issues>`_


Credits
=======

- Current maintainer: `Matt Carlton <https://github.com/mcarlton00>`_
- Original author: `Marvin Steadfast <https://github.com/xsteadfastx>`_
- `Contributors <https://github.com/jellyfin/mopidy-jellyfin/graphs/contributors>`_
