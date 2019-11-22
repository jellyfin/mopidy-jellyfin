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
    - There is some inconsistency in M.A.L.P. where you may have to go to the menu and select 'Show All Tracks' for the library to populate properly
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

The ``libraries`` option determines what is populated into Mopidy's internal library (view by Artists/Album/etc).  Using the file browser will show all libraries in the Jellyfin server that have a 'music' type.

It's also possible to add a hidden user by adding ``user_id = $id_number`` in addition to the username.  The user_id can be found through the web UI by navigating to your profile in the Web client and looking at the URL: ``https://jellyfin.example.com/web/index.html#!/myprofile.html?userId=3920b99003194448a2a9d4f0bedd3d82``

In this example, the config file will look like this::

    [jellyfin]
    hostname = Jellyfin server hostname
    port = Jellyfin server port
    username = username
    password = password
    user_id = 3920b99003194448a2a9d4f0bedd3d82
    libraries = Library1, Library2 (Optional: will default to "Music" if left undefined)


Development
===========

1. Install mopidy to your host system, preferably using the native package manager.  This handles all of the required dependencies.

2. Clone the repo to your local workstation

   ``$ git clone git@github.com:jellyfin/mopidy-jellyfin.git && cd mopidy-jellyfin``

2. Set up a virtualenv.  We need to include system packages since some things don't behave well inside of a virtualenv (such as ``PyGObject`` or interacting with pulseaudio).

   ``$ virtualenv --python python2.7 --system-site-packages env``

3. Install mopidy-jellyfin to the virtualenv.

   ``$ env/bin/python setup.py develop```

4. Do your thing.


Project resources
=================

- `Source code <https://github.com/jellyfin/mopidy-jellyfin>`_
- `Issue tracker <https://github.com/jellyfin/mopidy-jellyfin/issues>`_


Credits
=======

- Current maintainer: `Matt Carlton <https://github.com/mcarlton00>`_
- Original author: `Marvin Steadfast <https://github.com/xsteadfastx>`_
- `Contributors <https://github.com/jellyfin/mopidy-jellyfin/graphs/contributors>`_
