from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Jellyfin',
    version=get_version('mopidy_jellyfin/__init__.py'),
    url='https://github.com/jellyfin/mopidy-jellyfin',
    license='Apache License, Version 2.0',
    author='Matt Carlton',
    author_email='mcarlton00@gmail.com',
    description='Mopidy extension for playing music from jellyfin',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 2.0',
        'Pykka >= 1.1',
        'requests >= 2.20',
        'unidecode >= 1.1',
        'websocket-client >= 0.57'
    ],
    entry_points={
        'mopidy.ext': [
            'jellyfin = mopidy_jellyfin:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
