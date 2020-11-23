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

# Third party imports

# Local application imports
from dugu.utils import (
    find_files_recursively,
    hash_string,
    iteritems,
    os_path,
    _exit,
)


# ----------------------------------------------------------------------


class DuGuFileInfo:
    """ It handles the generated jobs from DuGuScan() class,
    whether from a single process or a multiple ones """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, file: str = '', size: int = 0, date: str = '', _hash: str = '') -> None:
        self.__file = file
        self.__size = size
        self.__date = date
        self.__hash = _hash
        self.__logs = []
        self.__has_info = True if file and size and date and _hash else False

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def file(self) -> str: return self.__file

    @property
    def size(self) -> int: return self.__size

    @property
    def date(self) -> str: return self.__date

    @property
    def hash(self) -> str: return self.__hash

    # ------------------------------
    #           PUBLIC
    # ------------------------------

    # -----------( LOGS )-----------

    def add_log(self, log_msg='') -> None:
        if log_msg:
            self.__logs.append(log_msg)

    def has_logs(self) -> bool:
        return len(self.__logs) > 0

    def logs(self) -> list:
        return self.__logs

    # --------( FILE INFO )---------

    def set_info(self, f_name='', f_size=0, f_date='', f_hash='') -> None:
        self.__file = f_name
        self.__size = f_size
        self.__date = f_date
        self.__hash = f_hash
        self.__has_info = True

    def has_info(self) -> bool:
        return self.__has_info


# ----------------------------------------------------------------------


class DuGuScannedData:

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, cwd='', which=None, show_progress=True, follow_symlinks=False) -> None:
        # [filepath1, filepath2, .., filepathN]
        self.__files_list = find_files_recursively(path=cwd, which=which, show_progress=show_progress,
                                                   follow_links=follow_symlinks)

        self.__hashes_list = []

        self.__total_files = len(self.__files_list)

        # {filepath: [size, date, hash], ..}
        self.__metadata = {}

        # total found files size
        self.__total_size = 0

        # store all hashes in one variable to re-hash it, to generate a unique id
        self.__all_hashes = ''

    # len()
    def __len__(self) -> int:
        return self.__total_files

    # +=
    def __iadd__(self, result=DuGuFileInfo):
        if result and type(result) is DuGuFileInfo:
            self.__metadata[result.file] = [result.size, result.date, result.hash]
            self.__total_size += result.size
            self.__all_hashes += '%s;' % result.hash
            self.__hashes_list.append(result.hash)
        return self

    # in
    def __contains__(self, item) -> bool:
        return item in self.__files_list

    # ---( COMPARISON OPERATORS )---

    def __lt__(self, other) -> bool: return self.__total_files < other
    def __le__(self, other) -> bool: return self.__total_files <= other
    def __gt__(self, other) -> bool: return self.__total_files > other
    def __ge__(self, other) -> bool: return self.__total_files >= other
    def __eq__(self, other) -> bool: return self.__total_files == other
    def __ne__(self, other) -> bool: return self.__total_files != other

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def files(self) -> list:
        """ Return a list of the found files.

            Ex: [filepath1, filepath2, .., filepathN]."""

        return self.__files_list

    @property
    def hashes(self) -> list:
        """ Return a list of the found files hashes.

            Ex: [hash1, hash2, .., hashN]."""

        return self.__hashes_list

    @property
    def metadata(self) -> dict:
        """ Return a dict of files info indexed by files.

            Ex: {filepath: [size, date, hash], ..}"""

        return self.__metadata

    @property
    def size(self) -> int:
        """ Return the total found files size. """

        return self.__total_size

    # ------------------------------
    #           PUBLIC
    # ------------------------------

    def id(self) -> str:
        """ Return a unique id of the scanned files. """

        return hash_string(string=self.__all_hashes, hash_type='md5')

    def reset(self) -> None:
        self.__metadata = {}
        self.__total_size = 0
        self.__all_hashes = ''


# ----------------------------------------------------------------------


class DuGuDuplicatesData:

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, total_files=0, hash_type='') -> None:
        # did it calculate the result
        self.__calculated = False

        # DuGuScanResult().total_files
        self.__total_files = total_files

        # (old name: hash_type)
        self.__hash_type = hash_type

        # how many duplicate sets (old name: dups_sets)
        self.__duplicate_sets = 0

        # how many duplicates (old name: dups_count)
        self.__total_duplicates = 0

        # what's the size of the duplicates (old name: dups_size)
        self.__duplicates_size = 0

        # {hash: [filepath1, filepath2, ..., filepathN], ...}
        self.__duplicated_files = {}

        # {hash: [filepath1, filepath2, ..., filepathN], ...} (old name: tmp_dup_list)
        self.__tmp_dup_list = {}

    def __len__(self) -> int:
        """ Return the total found duplicates. """

        return self.__total_duplicates

    def __contains__(self, item) -> bool:
        return item in self.__duplicated_files

    # ---( COMPARISON OPERATORS )---

    def __lt__(self, other): return self.__total_duplicates < other

    def __le__(self, other): return self.__total_duplicates <= other

    def __gt__(self, other): return self.__total_duplicates > other

    def __ge__(self, other): return self.__total_duplicates >= other

    def __eq__(self, other): return self.__total_duplicates == other

    def __ne__(self, other): return self.__total_duplicates != other

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def total_files(self) -> int:
        """ Return the total found files. """

        return self.__total_files

    @property
    def sets(self) -> int:
        """ Return the total sets of the found duplicates. """

        return self.__duplicate_sets if self.__duplicate_sets > 0 else len(self.__duplicated_files)

    @property
    def duplicates(self) -> int:
        """ Return the total found duplicates. """

        return self.__total_duplicates

    @property
    def size(self) -> int:
        """ Return the size of the total found duplicates. """

        return self.__duplicates_size

    @property
    def duplicated_files(self) -> dict:
        """ Return a dictionary of the duplicates indexed by their hashes.

            ex: {hash1: [filepath1, filepath2, ..., filepathN],
                ..,
                hashN: [filepath1, filepath2, ..., filepathN]}. """

        return self.__duplicated_files

    # ------------------------------
    #           PUBLIC
    # ------------------------------

    def check(self, result=DuGuFileInfo) -> bool:
        if result.hash in self.__tmp_dup_list:
            # if result.hash not in self.__duplicated_files:
            if result.hash not in self:
                self.__duplicated_files[result.hash] = []

            if self.__tmp_dup_list[result.hash] != result.file \
                    and self.__tmp_dup_list[result.hash] not in self.__duplicated_files[result.hash]:
                self.__duplicated_files[result.hash].append(self.__tmp_dup_list[result.hash])

            if result.file not in self.__duplicated_files[result.hash]:
                self.__duplicated_files[result.hash].append(result.file)

            return True
        else:
            self.__tmp_dup_list[result.hash] = result.file
            return False

    # TODO: implement this in multiprocessing ?
    def calculate(self) -> None:
        if not self.__calculated:
            count, size = 0, 0
            for sig, files in iteritems(self.__duplicated_files):
                count += len(files) - 1
                size += os_path.getsize(files[0]) * (len(files) - 1)

            self.__duplicate_sets = len(self.__duplicated_files)
            self.__total_duplicates = count
            self.__duplicates_size = size
            self.__calculated = True

    def reset(self):
        self.__duplicate_sets = 0
        self.__total_duplicates = 0
        self.__duplicates_size = 0
        self.__duplicated_files = {}
        self.__tmp_dup_list = {}
        self.__calculated = False


# ----------------------------------------------------------------------


class DuGuUniqueData:

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, src=DuGuScannedData(), dst=DuGuScannedData()) -> None:
        self.__metadata = {'src': {'id': src.id(), 'files': len(src), 'size': src.size},
                           'dst': {'id': dst.id(), 'files': len(dst), 'size': dst.size}}

        # list of unique files (full file path)
        # ex: ['filepath1', 'filepath2', .., 'filepathN']
        self.__files_list = []

        # dictionary of uniq files
        # ex: {'filepath1: [size, date, hash], ..}
        self.__files_info = {}

        # total unique size
        self.__files_size = 0

    def __iadd__(self, data: DuGuFileInfo = None):
        if data and type(data) is DuGuFileInfo and data.has_info():
            self.__files_list.append(data.file)
            self.__files_info[data.file] = [data.size, data.date, data.hash]
            self.__files_size += data.size
        return self

    # ------------------------------
    #          PROPERTIES
    # ------------------------------

    @property
    def src_metadata(self) -> dict: return self.__metadata['src']

    @property
    def src_id(self) -> str: return self.src_metadata['id']

    @property
    def src_files(self) -> int: return self.src_metadata['files']

    @property
    def src_size(self) -> int: return self.src_metadata['size']

    @property
    def dst_metadata(self) -> dict: return self.__metadata['dst']

    @property
    def dst_id(self) -> str: return self.dst_metadata['id']

    @property
    def dst_files(self) -> int: return self.dst_metadata['files']

    @property
    def dst_size(self) -> int: return self.dst_metadata['size']

    @property
    def files_list(self) -> list: return self.__files_list

    @property
    def files_info(self) -> dict: return self.__files_info

    @property
    def files_size(self) -> int: return self.__files_size

    # ------------------------------
    #             PUBLIC
    # ------------------------------

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    # ------------------------------
    #            PRIVATE
    # ------------------------------


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of DuGu package.')
    _exit('And is not meant to run directly.')
