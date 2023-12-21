#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# ----------------------------------------------------------------------
# Script:   DuGu (The Duplicates Guru)
# Version:  1.x.x
# Author:   DeaDSouL (Mubarak Alrashidi)
# URL:      https://unix.cafe/
# GitLab:   https://gitlab.com/DeaDSouL/dugu
# Twitter:  https://twitter.com/_DeaDSouL_
# License:  GPLv3
# ----------------------------------------------------------------------
# DuGu helps to you find, remove and avoid the duplicates.
# ----------------------------------------------------------------------


# Standard library imports
from __future__ import absolute_import
import time

# Third party imports

# Local application imports


# ----------------------------------------------------------------------


def static_vars(**kwargs):
    """ Used as a decorator to create static variables for a function.
            Ex: @static_vars(i=0, msg='some string'). """

    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


# ----------( DEBUG )-----------


def time_it(func):
    """ Used as a decorator to measure the elapsed time for a function.
            Ex: @time_it."""

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(func.__name__ + " took " + str((end-start)*1000) + " mil sec")
        return result
    return wrapper


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of dugu package.')
    exit('And is not meant to run directly.')
