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
from sys import version_info as _sys_version_info
from abc import ABC

# Third party imports

# Local application imports


# ----------------------------------------------------------------------


VERSION = '1.0.0'
__version__ = VERSION


# ----------------------------------------------------------------------


class _DuGuVersionABC(ABC):

    def __init__(self, float_comparison=False):
        self._comp_attr = 'full' if float_comparison else 'info'

    def __str__(self) -> str: return self.full

    def __repr__(self) -> str: return self.full

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def full(self) -> str: return str()
    @property
    def short(self) -> float or str: return float() or str()
    @property
    def info(self) -> tuple: return tuple()
    @property
    def major(self) -> int or str: return str()
    @property
    def minor(self) -> int or str: return str()
    @property
    def micro(self) -> int or str: return str()


# ----------------------------------------------------------------------


class _DuGuVersionComparison(_DuGuVersionABC):

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, float_comparison=False):
        super(_DuGuVersionComparison, self).__init__(float_comparison=float_comparison)

    def __lt__(self, other) -> bool:
        return self.__getattribute__(self._comp_attr) < getattr(self.__new_instance(other), self._comp_attr)

    def __le__(self, other) -> bool:
        return self.__getattribute__(self._comp_attr) <= getattr(self.__new_instance(other), self._comp_attr)

    def __gt__(self, other) -> bool:
        return self.__getattribute__(self._comp_attr) > getattr(self.__new_instance(other), self._comp_attr)

    def __ge__(self, other) -> bool:
        # print(' self: %s' % self.full)
        # print('other: %s' % self.__new_instance(other).full)
        # return self.full >= self.__new_instance(other).full
        # return self.info >= self.__new_instance(other).info
        return self.__getattribute__(self._comp_attr) >= getattr(self.__new_instance(other), self._comp_attr)

    def __eq__(self, other):
        return self.__getattribute__(self._comp_attr) == getattr(self.__new_instance(other), self._comp_attr)

    def __ne__(self, other) -> bool:
        return self.__getattribute__(self._comp_attr) != getattr(self.__new_instance(other), self._comp_attr)

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    @staticmethod
    def __new_instance(version=None) -> _DuGuVersionABC:
        # return version if type(version) is DuGuVersion else DuGuVersion(version)
        return version if isinstance(version, DuGuVersion) else DuGuVersion(version)


# ----------------------------------------------------------------------


class DuGuVersion(_DuGuVersionComparison):
    """ Returns 6 types of DuGu version levels:

        ex: the version is 1.2.3

            accessed by:        returned type   returned value
            obj.dugu.short:     float|str       1.2 or '1.2'
            obj.dugu.full:      str             '1.2.3'
            obj.dugu.major:     int|str         1 or '1'
            obj.dugu.minor:     int|str         2 or '2'
            obj.dugu.micro:     int|str         3 or '3'
            obj.dugu.info       tuple(int|str)  (1, 2, 3) or ('1', 2, '3') """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, version: (float or int or str or list or tuple) = VERSION, float_comparison=False) -> None:
        """ if float_comparison is True, then it will compare numbers as floats.
            Otherwise, it compares numbers as integers. (The versioning mode).

            Ex:
                float mode:     1.2.3 > 1.2.13
                    Because:    (1 == 1,    .2 == .2,   .3 > .13)

                versioning:     1.2.3 < 1.2.13
                    Because:    (1 == 1,    2 == 2,     3 < 13) """

        super(DuGuVersion, self).__init__(float_comparison=float_comparison)
        version = self.__prepare_version(version=version)
        nums = [num if num else '0' for num in version.split('.')]
        length = len(nums)
        if length < 3:
            for _ in range(3 - length):
                nums.append('0')

        self.__full = str().join('%s.' % num for num in nums)[:-1]  # [:-1] to remove latest dot '.'

        try:
            self.__short = float('%s.%s' % tuple(nums[:2]))
        except (TypeError, ValueError):
            self.__short = '%s.%s' % tuple(nums[:2])

        # nums = tuple(map(int, nums))    # either convert all elements or none
        for key, val in enumerate(nums):
            try:
                # ignore the IDE's 'Unexpected Type(s) error' regarding 'key' variable
                nums[key] = int(val)
            except (TypeError, ValueError):
                pass
        self.__info = tuple(nums)

    # ------------------------------
    #           PROPERTIES
    # ------------------------------

    @property
    def full(self) -> str:
        return self.__full

    @property
    def short(self) -> float or str:
        try:
            return float(self.__short)
        except (TypeError, ValueError):
            return self.__short

    @property
    def info(self) -> tuple:
        return self.__info

    @property
    def major(self) -> int or str:
        return self.__get_version_part(part='major')

    @property
    def minor(self) -> int or str:
        return self.__get_version_part(part='minor')

    @property
    def micro(self) -> int or str:
        return self.__get_version_part(part='micro')

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    @staticmethod
    def __prepare_version(version=None) -> str:
        t = type(version)

        if t is float:
            # return '%f.0' % version   # 1.0 -> 1.000000.0
            return '%s.0' % version     # 1.0 -> 1.0.0
        elif t is int:
            return '%d.0.0' % version
        elif t is str:
            if '.' not in version:
                version = '%s.0.0' % version
            return version
        elif t in (list, tuple):
            # [:-1] -> to remove latest dot '.'
            return ''.join('%s.' % (str(v) if v and type(v) in (int, float, str) else '0') for v in version)[:-1]
        else:  # None or anything else
            return '0.0.0'

    def __get_version_part(self, part: str = 'major' or 'minor' or 'micro') -> int or str:
        parts = {'major': 0, 'minor': 1, 'micro': 2}
        if not part or part not in parts:
            part = parts['major']
        try:
            return int(self.__info[part])
        except (TypeError, ValueError):
            return self.__info[part]


# ----------------------------------------------------------------------


class Version(DuGuVersion):
    def __init__(self, version=None, float_comparison=False):
        super(Version, self).__init__(version=version, float_comparison=float_comparison)


# ----------------------------------------------------------------------


class PythonVersion(_DuGuVersionComparison):
    """ Returns 6 types of Python version levels:

        ex: the version is 1.2.3

            accessed by:        returned type   returned value
            obj.py.short:       float           1.2
            obj.py.full:        str             '1.2.3'
            obj.py.major:       int             1
            obj.py.minor:       int             2
            obj.py.micro:       int             3
            obj.py.info         tuple           (1,2,3) """

    @property
    def full(self) -> str: return '%d.%d.%d' % _sys_version_info[0:3]

    @property
    def short(self) -> float: return float('%d.%d' % _sys_version_info[0:2])

    @property
    def info(self) -> tuple: return _sys_version_info[0:3]

    @property
    def major(self) -> int: return _sys_version_info.major

    @property
    def minor(self) -> int: return _sys_version_info.minor

    @property
    def micro(self) -> int: return _sys_version_info.micro


# ----------------------------------------------------------------------


class _Ver(object):
    """ Returns 6 types of version levels:

        ex: the version is 1.2.3

        for DuGu:
            accessed by:        returned type   returned value
            obj.dugu.short:     float|str       1.2 or '1.2'
            obj.dugu.full:      str             '1.2.3'
            obj.dugu.major:     int|str         1 or '1'
            obj.dugu.minor:     int|str         2 or '2'
            obj.dugu.micro:     int|str         3 or '3'
            obj.dugu.info       tuple(int|str)  (1, 2, 3) or ('1', 2, '3')

        for python:
            accessed by:        returned type   returned value
            obj.py.short:       float           1.2
            obj.py.full:        str             '1.2.3'
            obj.py.major:       int             1
            obj.py.minor:       int             2
            obj.py.micro:       int             3
            obj.py.info         tuple           (1,2,3) """

    def __init__(self, version=VERSION, float_comparison=False):
        self.__dugu_version = DuGuVersion(version=version, float_comparison=float_comparison)
        self.__python_version = PythonVersion()

    @property
    def py(self) -> PythonVersion: return self.__python_version

    @property
    def python(self) -> PythonVersion: return self.py

    @property
    def dugu(self) -> DuGuVersion: return self.__dugu_version


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of DuGu package.')
    exit('And is not meant to run directly.')

ver = _Ver(version=VERSION)
