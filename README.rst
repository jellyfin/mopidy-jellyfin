****************************
Mopidy-Emby
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Emby.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Emby/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/xsteadfastx/mopidy-emby/master.svg?style=flat
    :target: https://travis-ci.org/xsteadfastx/mopidy-emby
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/xsteadfastx/mopidy-emby/master.svg?style=flat
    :target: https://coveralls.io/r/xsteadfastx/mopidy-emby
    :alt: Test coverage

.. image:: https://img.shields.io/badge/SayThanks.io-%E2%98%BC-1EAEDB.svg
    :target: https://saythanks.io/to/xsteadfastx
    :alt: Say Thanks


Mopidy extension for playing music from Emby


Installation
============

Install by running::

    pip install Mopidy-Emby

or straight from GitHub::

    pip install git+https://github.com/xsteadfastx/mopidy-emby#egg=mopidy-emby


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Emby to your Mopidy configuration file::

    [emby]
    hostname = Emby server hostname
    port = Emby server port
    username = username
    password = password


TODO
====

- Searching is not implemented right now


Project resources
=================

- `Source code <https://github.com/xsteadfastx/mopidy-emby>`_
- `Issue tracker <https://github.com/xsteadfastx/mopidy-emby/issues>`_


Credits
=======

- Original author: `Marvin Steadfast <https://github.com/xsteadfastx>`_
- Current maintainer: `Marvin Steadfast <https://github.com/xsteadfastx>`_
- `Contributors <https://github.com/xsteadfastx/mopidy-emby/graphs/contributors>`_


Changelog
=========

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
