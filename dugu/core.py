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
import concurrent.futures
from os import (
    path as os_path,
)
from shutil import (
    disk_usage as shutil_disk_usage,
    rmtree,
)

# Third party imports

# Local application imports
from dugu.constants import (
    MAX_LINE_COLUMNS,
    MAX_USED_CPU_CORES,
    DUGU_UNIQUE_FILES_DIR,
)
from dugu.data import (
    DuGuFileInfo,
    DuGuScannedData,
    DuGuDuplicatesData,
    DuGuUniqueData,
)
from dugu.workers import DuGuWorker
from dugu.cache import (
    DuGuCache,
    DuGuDuplicatesCache,
    DuGuUniqueCache,
)
from dugu.utils import (
    has_multiple_cores,
    get_dir_size,
    path_is,
    bytes_to_readable_units,
    copy_directory_structures,
    copy_file_to_replicant,
    remove_empty_dirs,
    exit,
)
from dugu.io_input import (
    prompt,
    args_namespace,
)
from dugu.io_output import (
    waiting_indicator,
    _print as p,
    _print_fixed as pf,
    reprint as rp,
    reprint_fixed as rpf,
    log as log,
)


# ----------------------------------------------------------------------


class DuGuBaseCore:
    """ The main DuGu base core object """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args=args_namespace(), cwd=None) -> None:
        """ Prepare the base properties. """

        # app vars
        self._args = args
        self._first_run = True
        self._need_scan = False
        self._has_multiple_cores = has_multiple_cores()
        self._cwd = os_path.abspath(cwd)

        if not self.__passed_checks(args=args, cwd=cwd):
            exit('Exiting,..', status=1)

    # ------------------------------
    #           PROPERTIES
    # ------------------------------

    @property
    def cwd(self) -> str:
        return self._cwd

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    def __passed_checks(self, args=args_namespace(), cwd=None) -> bool:
        """ Return True if all given parameters are valid, otherwise return False. """

        if not args or type(args) is not args_namespace():
            p('Invalid Object(args): %s' % args)
            return False
        if cwd and not path_is(paths=cwd, checks='Edr', verbose=args.verbose):
            p('Invalid DIR: %s' % cwd)
            return False

        return self._hk_extra_checks()

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    # ----------( HOOKS )-----------

    def _hk_extra_checks(self) -> bool:
        return True


# ----------------------------------------------------------------------


class DuGuScanCore(DuGuBaseCore):
    """ The main scan core object """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    # TODO: remove the un-needed properties
    def __init__(self, args=args_namespace(), cwd=None, scan_type=None, desc='Scan') -> None:
        """ Prepare stuff for the action object.

            args: is the argparse.Namespace.
            cwd: is the target directory.
            scan_type: is one of 'SRC' or 'DST'.
            desc: is one of: 'Scan', 'Dups', 'SRC' or 'DST'. """

        super(DuGuScanCore, self).__init__(args=args, cwd=cwd)

        self._scan_cache = DuGuCache(args=args, cwd=cwd, _type='scan', cache_desc=desc)

        if scan_type and scan_type.upper() in ('SRC', 'DST'):
            self.__scan_type = '%s ' % scan_type.upper()
        else:
            self.__scan_type = ''

        self._report_dir = ''

        self._scan_result = DuGuScannedData(cwd=self._cwd, which=self.__scan_type.strip(), show_progress=True,
                                            follow_symlinks=self._args.follow_symlinks)

    # ------------------------------
    #           PROPERTIES
    # ------------------------------

    @property
    def scan_result(self) -> DuGuScannedData:
        return self._scan_result

    # ------------------------------
    #             PUBLIC
    # ------------------------------

    def start(self) -> None:
        """ Either load the cache if it's valid, or start the scan process. """

        if not self._first_run:
            self._reset()

        if self._args.force:
            self._init_scan()
        else:
            if self._scan_cache.load(against=self._scan_result):
                self._scan_result = self._scan_cache.content
                self._hk_if__cache_is_loaded()
            else:
                self._init_scan()

        self._first_run = False
        return

    def result(self) -> DuGuScannedData or (DuGuScannedData, DuGuDuplicatesData) or DuGuUniqueData:
        """ Return self._scan_result """

        return self._scan_result

    # ------------------------------
    #           PROTECTED
    # ------------------------------

    def _init_scan(self) -> None:
        """ The actual start of the scan process when there is no cache or it's not valid. """

        self._scan_cache.remove()
        self._hk_before__init_scan()

        i = 0
        if self._has_multiple_cores:
            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_USED_CPU_CORES) as executor:
                workers = [executor.submit(DuGuWorker.scrub_file, f, self._args)
                           for f in self._scan_result.files]
                for worker in concurrent.futures.as_completed(workers):
                    i = self.__progress(i)
                    self.__process_result(worker.result())
        else:
            for file in iter(self._scan_result.files):
                i = self.__progress(i)
                self.__process_result(DuGuWorker.scrub_file(file, self._args))

        pf('Scanning %sFiles' % self.__scan_type, status='Done',
           suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        if self._scan_cache.save(self._scan_result):
            # TODO: log -> save done
            pass
        else:
            # TODO: log -> save failed
            pass
        self._hk_after__init_scan()

        return

    def _reset(self) -> None:
        """ Reset DuGuScanResult instance's property, & call a hook (_hk_after__reset()) """

        self._scan_result.reset()
        self._hk_after__reset()
        return

    # ----------( HOOKS )-----------

    def _hk_if__cache_is_loaded(self) -> None:
        pass

    def _hk_before__init_scan(self) -> None:
        self.__need_scan = True

    def _hk_after__init_scan(self) -> None:
        pass

    def _hk_if__result_has_info(self, result=DuGuFileInfo()) -> None:
        pass

    def _hk_after__reset(self) -> None:
        pass

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    def __process_result(self, result=DuGuFileInfo()) -> None:
        if type(result) != DuGuFileInfo:
            return

        # printing logs
        if result.has_logs():
            for log_msg in result.logs():
                log(msg=log_msg, verbose=self._args.verbose, re_print=True)

        # registering hash & file
        if result.has_info():
            self._scan_result += result
            self._hk_if__result_has_info(result=result)

        return

    def __progress(self, i=0) -> int:
        """ Prints current progress, and return the next int(i) """

        i += 1
        rp('Scanning %sFiles: (%d/%d) - %d%% \r' % (self.__scan_type, i, len(self._scan_result),
                                                    (i * 100 / len(self._scan_result))))
        return i


# ----------------------------------------------------------------------


class DuGuDuplicatesCore(DuGuScanCore):
    """ The main duplicates core object """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args=args_namespace()) -> None:
        """ Prepare stuff for the finding duplicates process """

        super(DuGuDuplicatesCore, self).__init__(args=args, cwd=args.DIR, scan_type='')

        self._dups_cache = DuGuDuplicatesCache(args=args, cwd=args.DIR, _type='dups', cache_desc='Dups')

        self._dups_result = DuGuDuplicatesData(total_files=len(self._scan_result), hash_type=self._args.hashtype)

    # ------------------------------
    #           PROPERTIES
    # ------------------------------

    @property
    def duplicates_result(self) -> DuGuDuplicatesData:
        return self._dups_result

    # ------------------------------
    #             PUBLIC
    # ------------------------------

    def result(self) -> (DuGuScannedData, DuGuDuplicatesData):
        """ Returns self._scan_result & self._dups_result respectively """

        return self._scan_result, self._dups_result

    # ------------------------------
    #             HOOKS
    # ------------------------------

    def _hk_if__cache_is_loaded(self) -> None:
        if self._dups_cache.load():
            self._dups_result = self._dups_cache.content
        else:
            self._init_scan()

    def _hk_before__init_scan(self) -> None:
        if self._dups_cache.remove():
            # TODO: log -> remove -> done
            pass
        else:
            # TODO: log -> remove -> failed
            pass
        # TODO: do we really need it??
        self.__need_scan = True

    def _hk_after__init_scan(self) -> None:
        self._dups_result.calculate()
        if self._dups_cache.save(self.duplicates_result):
            # TODO: log -> save -> done
            pass
        else:
            # TODO: log -> save -> failed
            pass

    def _hk_if__result_has_info(self, result=DuGuFileInfo()) -> None:
        self._dups_result.check(result=result)

    def _hk_after__reset(self) -> None:
        self._dups_result.reset()

    # ------------------------------
    #           UN-NEEDED
    # ------------------------------


# ----------------------------------------------------------------------


class DuGuUniqueCore(DuGuBaseCore):
    """ The main pre-copy core object """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args=args_namespace()) -> None:
        """ Prepare stuff for the pre-copying process """

        self._unique_path = os_path.join(os_path.abspath(args.DIRS[0]), DUGU_UNIQUE_FILES_DIR)

        super(DuGuUniqueCore, self).__init__(args=args, cwd=args.DIRS[1])

        # 0: src, 1: dst
        self._src_scan = DuGuScanCore(args=args, cwd=args.DIRS[0], scan_type='src', desc='SRC')
        self._src_scan.start()  # must be after: super()

        self._dst_scan = DuGuScanCore(args=args, cwd=args.DIRS[1], scan_type='dst', desc='DST')
        self._dst_scan.start()  # must be after: super()

        # must be after:    self._src_scan.start() AND self._dst_scan.start()
        if not self.__cp_src_dir_structure():
            exit('Aborting,..', status=1)

        self._unique_result = DuGuUniqueData(src=self.src_result, dst=self.dst_result)
        self._unique_cache = DuGuUniqueCache(args=args, cwd=self.dst_path, _type='precopy', cache_desc='Unique')

        self._not_copied_files = []

    # ------------------------------
    #           PROPERTIES
    # ------------------------------

    @property
    def src_result(self) -> DuGuScannedData:
        return self._src_scan.result()

    @property
    def src_path(self) -> str:
        return self._src_scan.cwd

    @property
    def dst_result(self) -> DuGuScannedData:
        return self._dst_scan.result()

    @property
    def dst_path(self) -> str:
        return self._dst_scan.cwd

    @property
    def unique_result(self) -> DuGuUniqueData:
        return self._unique_result

    @property
    def unique_path(self) -> str:
        return self._unique_path

    @property
    def not_copied_files(self) -> list:
        return self._not_copied_files

    # ------------------------------
    #             PUBLIC
    # ------------------------------

    def result(self) -> (DuGuScannedData, DuGuScannedData, DuGuUniqueData):
        """ Returns self._src_scan.result & self._dst_scan.result & self._unique_result respectively """

        return self._src_scan.result(), self._dst_scan.result(), self._unique_result

    # ------------------------------

    def start(self) -> None:
        """ Either load the cache if it's valid, or start the finding unique files process. """

        # if not self._first_run:
        #     self._reset()

        if self._args.force:
            self.__find_uniques()
        else:
            if self._unique_cache.load(against_src=self.src_result,
                                       against_dst=self.dst_result):
                self._unique_result = self._unique_cache.content
                if len(self._unique_result.files_list) > 0:
                    self.__copy_uniques()
                remove_empty_dirs(path=self._unique_path, remove_base_dir=False, verbose=self._args.verbose,
                                  re_print=False)
            else:
                self.__find_uniques()

        self._first_run = False
        return

    # ------------------------------
    #             HOOKS
    # ------------------------------

    def _hk_extra_checks(self) -> bool:
        """ Preform the necessary checks that the 'copy action' needs to function properly.
            Then return True if all of them were passed, otherwise return False. """

        # src checks (must be: dir, readable, writable)
        if not path_is(paths=self._args.DIRS[0], checks='Edrw', verbose=self._args.verbose, re_print=False, log_lvl=0):
            return False

        # dst checks (must be: dir, readable)
        if not path_is(paths=self._args.DIRS[1], checks='Edr', verbose=self._args.verbose, re_print=False, log_lvl=0):
            return False

        # handle old unique-dir, if it exists
        if os_path.exists(self._unique_path):
            answer = prompt(msgs='"%s" exists! Do you want to remove it first? (y/n): ' % self._unique_path,
                            choices=('y', 'n'), verbose=self._args.verbose, re_print=True)
            if answer == 'n':
                log(msg='Can not proceed while: "%s" exists!' % self._unique_path, verbose=self._args.verbose,
                    re_print=False, lvl=0)
                return False
            else:
                p(' ')
                rmtree(self._unique_path)

        # make sure we have enough space
        disk_available_space = shutil_disk_usage(self._args.DIRS[0]).free
        src_size = get_dir_size(dir_path=self._args.DIRS[0], follow_links=self._args.follow_symlinks,
                                show_progress=True, verbose=self._args.verbose, re_print=True)
        if disk_available_space <= src_size:
            log(msg='Canceling the copy process. Since the available disk space in "%s" is (%s) which is less than the '
                    'minimum required space (%s).!' % (self._args.DIRS[0],
                                                       bytes_to_readable_units(disk_available_space),
                                                       bytes_to_readable_units(src_size)),
                verbose=self._args.verbose, re_print=False, lvl=1)
            return False

        return True

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    def __find_uniques(self) -> None:
        if self._unique_cache.remove():
            # TODO: log -> remove -> done
            pass
        else:
            # TODO: log -> remove -> failed
            pass
        # TODO: do we really need it??
        self.__need_scan = True

        msg = 'Finding Unique Files'
        for file, info in self._src_scan.result().metadata.items():
            rpf(msg=msg, status=' %s' % waiting_indicator(), suffix=' \r', max_cols=MAX_LINE_COLUMNS)
            if info[2] not in self._dst_scan.result().hashes:
                self._unique_result += DuGuFileInfo(file=file, size=info[0], date=info[1], _hash=info[2])

        if len(self._unique_result.files_list) > 0:
            pf(msg=msg, status='Done', suffix=' \r', max_cols=MAX_LINE_COLUMNS)
            self.__copy_uniques()
        else:
            pf(msg=msg, status='None', suffix=' \r', max_cols=MAX_LINE_COLUMNS)

        remove_empty_dirs(path=self._unique_path, remove_base_dir=False, verbose=self._args.verbose, re_print=False)

        if self._unique_cache.save(self._unique_result):
            # TODO: log -> save -> done
            pass
        else:
            # TODO: log -> save -> failed
            pass

    def __copy_uniques(self):
        total = len(self._unique_result.files_list)
        i = 0

        for file in self._unique_result.files_list:
            i += 1
            rp('Copying Unique Files: (%d/%d) - %d%% \r' % (i, total, (i * 100 / total)))
            if not copy_file_to_replicant(file=file, start_dir=self.src_path, dst_dir=self.unique_path,
                                          follow_symlinks=self._args.symlinks, verbose=self._args.verbose,
                                          re_print=True):
                self._not_copied_files.append(file)
        pf('Copying Unique Files', status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        return

    def __cp_src_dir_structure(self) -> bool:
        """ Return True if we successfully copied the Source-Directory's structure
            to the unique directory's path. Otherwise, return False. """

        status = 'Done'
        rpf('Copying Src Structure', suffix=' \r', max_cols=MAX_LINE_COLUMNS)
        # TODO: maybe we need to exit if there is any none-readable directory
        if not copy_directory_structures(src=self._args.DIRS[0], dst=self._unique_path, re_print=True,
                                         copy_symlinks=not self._args.follow_symlinks, verbose=self._args.verbose):
            log(msg='Could not copy the "%s" structure to "%s" !!' % (self._args.DIRS[0], self._unique_path),
                verbose=self._args.verbose, re_print=False, lvl=1)
            status = 'Fail'

        pf('Copying Src Structure', status=status, suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        return True if status == 'Done' else False

    # ------------------------------
    #           UN-NEEDED
    # ------------------------------


# ----------------------------------------------------------------------


if __name__ == '__main__':
    p('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
