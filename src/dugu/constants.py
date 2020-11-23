#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# ----------------------------------------------------------------------
# Script:   DuGu (The Duplicates Guru)
# Version:  1.x.x
# Author:   DeaDSouL (Mubarak Alrashidi)
# URL:      https://unix.cafe/
# GitHub:   https://github.com/DeaDSouL/dugu
# Twitter:  https://twitter.com/_DeaDSouL_
# License:  GPLv3
# ----------------------------------------------------------------------
# DuGu helps to you find, remove and avoid the duplicates.
# ----------------------------------------------------------------------


# Standard library imports
from __future__ import absolute_import, print_function
from os import path as os_path
from tempfile import gettempdir
from getpass import getuser

# Third party imports

# Local application imports
from dugu.version import (
    ver,
    Version,
)


# ----------------------------------------------------------------------


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_LINE_COLUMNS = 35
MAX_USED_CPU_CORES = 6

DEFAULT_TMP_PATH = os_path.abspath(gettempdir())
DUGU_DIR_NAME = 'dugu_%s' % getuser()
DUGU_BASE_PATH = os_path.join(DEFAULT_TMP_PATH, DUGU_DIR_NAME)

DUGU_CACHE_DIR = 'cache'
DUGU_CACHE_PATH = os_path.join(DUGU_BASE_PATH, DUGU_CACHE_DIR)

DUGU_ISOLATION_DIR = 'isolated'
DUGU_ISOLATION_PATH = os_path.join(DUGU_BASE_PATH, DUGU_ISOLATION_DIR)

DUGU_SOFT_LINKS_DIR = 'soft-links'
DUGU_SOFT_LINKS_PATH = os_path.join(DUGU_BASE_PATH, DUGU_SOFT_LINKS_DIR)

DUGU_HARD_LINKS_DIR = 'hard-links'
DUGU_HARD_LINKS_PATH = os_path.join(DUGU_BASE_PATH, DUGU_HARD_LINKS_DIR)

DUGU_UNIQUE_FILES_DIR = '_UniqueFiles_'

# ----------------------------------------------------------------------

DUGU_NEEDED_DIRS = (DUGU_CACHE_PATH, DUGU_ISOLATION_PATH, DUGU_SOFT_LINKS_PATH, DUGU_HARD_LINKS_PATH)

# ----------------------------------------------------------------------

REQUIRED_PYTHON_VERSION = Version(version='3.8.6', float_comparison=False)
CURRENT_PYTHON_VERSION = ver.python
DUGU_VERSION = ver.dugu


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
