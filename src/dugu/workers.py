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
from stat import S_ISSOCK
from time import (
    strftime as time_strftime,
    localtime as time_localtime
)
from os import (
    path as os_path,
    access as os_access,
    R_OK,
    stat as os_stat
)

# Third party imports

# Local application imports
from dugu.data import (
    DuGuFileInfo
)
from dugu.utils import (
    hash_file_contents,
)
from dugu.constants import (
    DATETIME_FORMAT
)


# ----------------------------------------------------------------------


class DuGuWorker:

    # ------------------------------
    #            JOBS
    # ------------------------------

    @staticmethod
    def scrub_file(file_path=None, args=None) -> DuGuFileInfo:
        """ Extracts file_path, size, modified_datetime and hash of a given file """

        ret = DuGuFileInfo()
        if not file_path:
            return ret
        ff = os_path.abspath(file_path)

        if os_path.islink(ff):
            if not args.symlinks:
                ret.add_log('Ignoring Link: %s' % ff)
                return ret
            # otherwise, read the link
            anti_link_loop = []
            while os_path.islink(ff):
                anti_link_loop.append(ff)
                ff = os_path.realpath(ff)
                if ff in anti_link_loop:
                    ret.add_log('Ignoring Infinite link loop: %s' % ff)
                    return ret
                if os_path.isdir(ff):
                    return ret

        if not os_path.exists(ff):
            ret.add_log('Ignoring Inexistent: %s' % ff)

        elif not os_access(ff, R_OK):
            ret.add_log('Ignoring Unreadable: %s' % ff)

        elif S_ISSOCK(os_stat(ff).st_mode):
            ret.add_log('Ignoring Socket: %s' % ff)

        elif os_path.isfile(ff):
            dt_modified = time_strftime(DATETIME_FORMAT, time_localtime(os_path.getmtime(ff)))
            size = os_path.getsize(ff)
            hash_sig = hash_file_contents(ff, args.hashtype)
            ret.set_info(f_name=ff, f_size=size, f_date=dt_modified, f_hash=hash_sig)
            # self.scan_result['files'][ff] = [size, dt_modified, hash_sig]

        else:
            ret.add_log('Unknown: %s' % ff)

        return ret


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
