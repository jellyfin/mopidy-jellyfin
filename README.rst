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
