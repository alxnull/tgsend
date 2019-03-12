#!/usr/bin/env python3

from setuptools import setup
from tgsend import __version__

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='tgsend',
    version=__version__,
    description='Send messages to Telegram chats from Python and the command line',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Alex C.P. (alxnull)',
    author_email="bluegrams@e.mail.de",
    license="BSD-3-Clause",
    url="https://github.com/alxnull/tgsend",
    py_modules=['tgsend'],
    entry_points={
        'console_scripts': ['tgsend = tgsend:main']
    },
    install_requires=[
        'requests'
    ],
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Topic :: Communications :: Chat",
        "Topic :: Utilities"
    ),
    keywords="telegram message"
)
