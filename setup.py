#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'dbus-python',
    'rpi-ws281x',
    'ruamel.yaml',
    'tinyrpc[gevent,wsgi]'
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Peter Rowlands",
    author_email='peter@pmrowla.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Aqours themed LED controller for Raspberry Pi.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='aqours itabag wota wotabag',
    name='wotabag',
    packages=find_packages(include=['wotabag']),
    entry_points={
        'console_scripts': [
            'wotabagd = wotabag.server:main',
        ]
    },
    setup_requires=setup_requirements,
    tests_require=test_requirements,
    url='https://github.com/pmrowla/wotabag',
    version='0.1.0',
    zip_safe=False,
)
