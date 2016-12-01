from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Emby',
    version=get_version('mopidy_emby/__init__.py'),
    url='https://github.com/xsteadfastx/mopidy-emby',
    license='Apache License, Version 2.0',
    author='Marvin Steadfast',
    author_email='marvin@xsteadfastx.org',
    description='Mopidy extension for playing music from Emby',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'requests >= 2.0',
    ],
    entry_points={
        'mopidy.ext': [
            'emby = mopidy_emby:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
