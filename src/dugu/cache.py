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
from __future__ import absolute_import
from time import (
    strftime as time_strftime,
    localtime as time_localtime,
)
import pickle

# Third party imports

# Local application imports
from dugu.app_input import args_namespace
from dugu.data import (
    DuGuScannedData,
    DuGuDuplicatesData,
    DuGuUniqueData,
)
from dugu.utils import (
    os_path,
    path_is,
    hashlib_md5,
    mkdir,
    remove_file,
    build_path,
)
from dugu.constants import (
    DATETIME_FORMAT,
    MAX_LINE_COLUMNS,
    DUGU_CACHE_DIR,
    DUGU_CACHE_PATH,
)
from dugu.app_output import (
    _print as p,
    _print_fixed as pf,
    reprint as rp,
    reprint_fixed as rpf,
    log,
)


# ----------------------------------------------------------------------


class DuGuCache(object):
    """ Main DuGu Cache Object. """

    _cache_type = DuGuScannedData or DuGuDuplicatesData or DuGuUniqueData
    _cache_kind = ''   # 'scan' | 'dups' | 'precopy'
    _cache_name = ''   # 'scan' | 'dups' | 'uniq'
    _cache_desc = ''   # '' | 'SRC' | 'DST'
    _cache_file = ''   # path of cache file
    _cache_data = DuGuScannedData or DuGuDuplicatesData or DuGuUniqueData

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args: args_namespace(), cwd: str = '', _type: str = '' or 'scan' or 'dups' or 'precopy',
                 cache_desc: str = 'Scan' or 'Dups' or 'SRC' or 'DST' or 'Unique') -> None:
        self._args = args
        self._cwd = os_path.abspath(cwd)  # To use its hash as an identifier for cache file
        self._cache_desc = '%s ' % cache_desc if cache_desc in ('Scan', 'Dups', 'SRC', 'DST', 'Unique') else ''
        self._cache_available = mkdir(DUGU_CACHE_PATH, verbose=self._args.verbose, check=True)

        if not self.is_available or not self.__set_metadata(_type=_type):
            self._cache_available = False
            log(msg="Caching feature won't be available.", verbose=self._args.verbose, lvl=1)

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def cache_dir(self) -> str:
        """ Return the default cache directory's name. (usually: DUGU_CACHE_DIR). """

        return DUGU_CACHE_DIR

    @property
    def cache_path(self) -> str:
        """ Return the default cache path. (usually: DUGU_CACHE_PATH). """

        return DUGU_CACHE_PATH

    @property
    def cwd(self) -> str:
        """ Return the CWD for the path we're caching its contents. """

        return self._cwd

    @property
    def is_available(self) -> bool:
        """ Return True if cache feature is available, otherwise False. """

        return self._cache_available

    @property
    def type(self) -> str:
        """ Return the cache kind which is one of:
            'scan', 'dups' or 'precopy'. """

        return self._cache_kind

    @property
    def name(self) -> str:
        """ Return the human readable short-name of the cache name.
            Which is one of: 'scan', 'dups' or 'uniq'. """

        return self._cache_name

    @property
    def file(self) -> str:
        """ Return the cache file including its path. """

        return self._cache_file

    @property
    def filename(self) -> str:
        """ Return the cache filename. Something like:
            dir-path-md5-hash_[md5|sha1|sha256|sha512]_[scan|dups|uniq].pkl.
            Ex: 79db3b68f33e4877b1b56dec92bc8796_md5_scan.pkl. """

        return os_path.basename(self._cache_file)

    @property
    def content(self) -> DuGuScannedData or DuGuDuplicatesData or DuGuUniqueData:
        """ Return the data object. Which is one of:
            dugu.data.DuGuScannedData(),
            dugu.data.DuGuDuplicatesData() or
            dugu.data.DuGuUniqueData(). """

        return self._cache_data

    # ------------------------------
    #           PUBLIC
    # ------------------------------

    def save(self, data=None) -> bool:
        """ Return True if the given valid data is saved successfully, otherwise return False. """

        if not data or not self.is_available or type(data) != self._cache_type:
            return False

        if self.exists():
            self.remove()

        try:
            pickle.dump(data, open(self._cache_file, 'wb'))
        except pickle.PicklingError as _:
            log(msg="Couldn't save the cache! Turning caching feature off.", verbose=self._args.verbose, lvl=1)
            self._cache_available = False
            return False

        return True

    def remove(self) -> bool:
        """ Return True if the existed cache file has been removed successfully, otherwise return False. """

        if not self.exists():
            return False

        rpf('Removing Old %sCache' % self._cache_desc, max_cols=MAX_LINE_COLUMNS)

        if not remove_file(self._cache_file):
            log("Couldn't remove '%s'!" % self._cache_file, verbose=self._args.verbose, lvl=1)
            rpf('Removing Old %sCache' % self._cache_desc, status='Fail', suffix='\n', max_cols=MAX_LINE_COLUMNS)
            return False

        rpf('Removing Old %sCache' % self._cache_desc, status='Done', suffix='\n', max_cols=MAX_LINE_COLUMNS)

        return True

    def exists(self) -> bool:
        """ Return True if cache file is an existed file, otherwise False. """

        return path_is(paths=self._cache_file, checks='Ef', verbose=self._args.verbose)

    def load(self, **kwargs) -> bool:
        """ Return True if the valid existed cache file is loaded, otherwise return False. """

        if not self.is_available or not self.exists():
            return False

        with open(self._cache_file, 'rb') as file_handler:
            if not file_handler.readable():
                log(msg="%s: is not readable." % self._cache_file, verbose=self._args.verbose, lvl=1)
                self.remove()
                return False

            loading_msg = 'Loading %sCache' % self._cache_desc

            try:
                self._cache_data = pickle.load(file_handler)
            except UnicodeDecodeError as _:
                log(msg="Failed loading: '%s'." % self._cache_file, verbose=self._args.verbose, lvl=1)
                pf(msg=loading_msg, status='Fail', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                self.remove()
                return False

        pf(msg=loading_msg, status='Done', suffix=' \r', max_cols=MAX_LINE_COLUMNS)

        if type(self._cache_data) != self._cache_type:
            pf('Validating %sCache Type' % self._cache_desc, status='Fail', suffix='\r', max_cols=MAX_LINE_COLUMNS)
            self.remove()
            return False
        else:
            pf('Validating %sCache Type' % self._cache_desc, status='Done', suffix='\r', max_cols=MAX_LINE_COLUMNS)

        # against   or   against_src & against_dst
        return self._is_validated(**locals()['kwargs'])

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    def _is_validated(self, against=None) -> bool:
        """ Return True if the cache file is valid, otherwise return False. """

        def __fail(s, cache_desc=''):
            pf('Validating %sCache Data' % cache_desc, status='Fail',
               suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
            s.remove()
            return False

        def __done(cache_desc=''):
            pf('Validating %sCache Data' % cache_desc, status='Done',
               suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
            return True

        if self._cache_type is DuGuScannedData:
            if len(self._cache_data) != len(against):
                if len(self._cache_data) > len(against):
                    pf('Missing Files Detected', status='Done', suffix='\r',
                       suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                if len(self._cache_data) < len(against):
                    pf('New Files Detected', status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                return __fail(self, cache_desc=self._cache_desc)

            i = 0

            # arr[0]=size, arr[1]=mtime, arr[2]=hash
            for file, arr in self._cache_data.metadata.items():
                i += 1
                rp('Validating %sCache: (%d/%d) - %d%% \r' % (self._cache_desc, i, len(self._cache_data),
                                                              (i * 100 / len(self._cache_data))))
                if not os_path.exists(file) or not os_path.isfile(file):
                    pf('Missing Files Detected', status='Done', suffix='\r',
                       suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                    return __fail(self, cache_desc=self._cache_desc)

                if arr[0] != os_path.getsize(file):
                    pf('Diff Sizes Detected', status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                    return __fail(self, cache_desc=self._cache_desc)

                if arr[1] != time_strftime(DATETIME_FORMAT, time_localtime(os_path.getmtime(file))):
                    pf('Diff mTime Detected', status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                    return __fail(self, cache_desc=self._cache_desc)

        return __done(cache_desc=self._cache_desc)

    # ------------------------------
    #           PRIVATE
    # ------------------------------

    def __set_metadata(self, _type='scan') -> bool:
        # if _type == 'scan' and hasattr(self._args, 'DIR'):
        if _type == 'scan':
            self._cache_type = DuGuScannedData
            self._cache_kind = 'scan'
            self._cache_name = 'scan'
        # elif _type == 'dups' and hasattr(self._args, 'DIR'):
        elif _type == 'dups':
            self._cache_type = DuGuDuplicatesData
            self._cache_kind = 'dups'
            self._cache_name = 'dups'
        # elif _type == 'precopy' and hasattr(self._args, 'DIRS'):
        elif _type == 'precopy':
            self._cache_type = DuGuUniqueData
            self._cache_kind = 'precopy'
            self._cache_name = 'uniq'
        else:
            return False

        self._cache_file = self.__get_cache_path()

        if path_is(paths=self._cache_file, checks='E', verbose=self._args.verbose):
            return path_is(paths=self._cache_file, checks='frw', verbose=self._args.verbose)
        else:
            return path_is(paths=os_path.dirname(self._cache_file),
                           checks='drw', verbose=self._args.verbose)

    def __get_cache_path(self) -> str:
        # (dir-md5-sig)_(md5|sha1|sha256|sha512)_(scan|dups|uniq).pkl
        sig = hashlib_md5(str(self._cwd).encode('utf-8')).hexdigest()
        cache_file = '%s_%s_%s.pkl' % (sig, self._args.hashtype, self._cache_name)

        return build_path(cache_file, self.cache_path)

    # ------------------------------
    #           UN-NEEDED
    # ------------------------------

    # ------------------------------


# ----------------------------------------------------------------------


class DuGuDuplicatesCache(DuGuCache):

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, **kwargs):
        super(DuGuDuplicatesCache, self).__init__(**kwargs)

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    def _is_validated(self, *args, **kwargs) -> bool:
        pf(msg='Validating Dups Cache Data', status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
        return True

# ----------------------------------------------------------------------


class DuGuUniqueCache(DuGuCache):

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args=None, cwd=None, _type='' or 'scan' or 'dups' or 'precopy',
                 cache_desc='Scan' or 'Dups' or 'SRC' or 'DST' or 'Unique') -> None:
        super(DuGuUniqueCache, self).__init__(args=args, cwd=cwd, _type=_type, cache_desc=cache_desc)

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    def _is_validated(self, against_src: DuGuScannedData = None, against_dst: DuGuScannedData = None) -> bool:
        """ Return True if the cache file is valid, otherwise return False. """

        # src
        if against_src and type(against_src) is DuGuScannedData:
            msg = 'Validating Unique Cache SRC'
            rpf(msg=msg, suffix=' \r', max_cols=MAX_LINE_COLUMNS)
            if against_src.id() != self._cache_data.src_id or \
                    against_src.size != self._cache_data.src_size or \
                    len(against_src) != self._cache_data.src_files:
                pf(msg=msg, status='Fail', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                self.remove()
                return False
            else:
                pf(msg=msg, status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        # dst
        if against_dst and type(against_dst) is DuGuScannedData:
            msg = 'Validating Unique Cache DST'
            rpf(msg=msg, suffix=' \r', max_cols=MAX_LINE_COLUMNS)
            if against_dst.id() != self._cache_data.dst_id or \
                    against_dst.size != self._cache_data.dst_size or \
                    len(against_dst) != self._cache_data.dst_files:
                pf(msg=msg, status='Fail', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
                self.remove()
                return False
            else:
                pf(msg=msg, status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        return True


# ----------------------------------------------------------------------


if __name__ == '__main__':
    p('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
