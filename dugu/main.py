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
from __future__ import (
    absolute_import,
    print_function,
)
import time

# Third party imports

# Local application imports
from dugu.action import (
    DuGuScanAction,
    DuGuPreCopyAction,
)
from dugu.version import ver
from dugu.constants import (
    DUGU_NEEDED_DIRS,
    DUGU_DIR_NAME,
    DUGU_BASE_PATH,
    MAX_LINE_COLUMNS,
    REQUIRED_PYTHON_VERSION,
    CURRENT_PYTHON_VERSION,
)
from dugu.utils import (
    os_path,
    mkdir,
    mktemp_dir,
    path_is,
    remove_empty_dirs,
    bytes_to_readable_units,
    exit,
)
from dugu.io_output import (
    _print as p,
    log as log,
    print_line as pl,
)
from dugu.io_input import (
    parse_args,
)


# ----------------------------------------------------------------------


class DuGuMain:

    def __init__(self) -> exit:
        import tracemalloc
        tracemalloc.start()
        t1_start = time.perf_counter()
        try:
            # init: args
            self.args = parse_args()
            self.__main()
        except KeyboardInterrupt as _:
            p('\nExiting,..')
        finally:
            t1_end = time.perf_counter()
            p('\nTook: {} seconds'.format(t1_end - t1_start))
            current, peak = tracemalloc.get_traced_memory()
            p(f"Current memory usage is {current / 10 ** 6}MB; Peak was {peak / 10 ** 6}MB")
            tracemalloc.stop()
            exit(status=0)

    def __main(self) -> None:
        """ Main method that handles the given CMD. """

        if self.args.verbose:
            log(msg='Verbosity mode is ON', verbose=self.args.verbose)

        self.__chk_requirements()
        self.__pre_main()

        if self.args.version:
            exit('DuGu Version: ' + ver.dugu.full + '\n', 0)
        elif self.args.cmd == 'scan':
            self.__action_scan()
        elif self.args.cmd == 'precopy':
            self.__action_precopy()
        else:
            exit('Incorrect CMD!', status=1)

        return

    def __pre_main(self) -> None:
        """ Create the needed directories, and prepare the given directory(s). """

        # Create the needed DuGu directories:
        # ex: (cache, isolation, soft-links and hard-links)
        for needed_dir in DUGU_NEEDED_DIRS:
            mkdir(needed_dir, verbose=self.args.verbose, check=True)

        # Remove trailing slash & use real-path if the dir(s) was a/were sym-link
        if self.args.cmd == 'scan':
            self.args.DIR = os_path.realpath(self.args.DIR)
        elif self.args.cmd == 'precopy':
            for key, path in enumerate(self.args.DIRS):
                self.args.DIRS[key] = os_path.realpath(path)

        p()
        return

    def __chk_requirements(self) -> None:
        """ Make sure we're using the minimum required version of python.
            And the pre-defined DuGu path is an existed usable directory. """

        if CURRENT_PYTHON_VERSION < REQUIRED_PYTHON_VERSION:
            exit(msg='Minimum required Python version is: %s not %s' % (REQUIRED_PYTHON_VERSION,
                                                                        CURRENT_PYTHON_VERSION), status=1)

        dugu_path = mktemp_dir(_dir=DUGU_DIR_NAME, verbose=self.args.verbose)
        if dugu_path != DUGU_BASE_PATH \
                or not path_is(paths=dugu_path, checks='Edrw', log_lvl=0,
                               verbose=self.args.verbose, re_print=False):
            exit('Could not use the pre-defined DuGu path!')

        return

    # ------------------------------------------------------------------
    #                           ACTIONS:
    # ------------------------------------------------------------------

    def __action_scan(self) -> None:
        """ Scan & find duplicates in given path. """

        scan_action = DuGuScanAction(args=self.args)
        scan_action.start()
        scan_data, dups_data = scan_action.result()

        if dups_data.duplicates == 0:
            p()
            pl(MAX_LINE_COLUMNS)
            p('No duplicates found.')
            pl(MAX_LINE_COLUMNS)
        else:
            gen_links_dir = None
            if self.args.soft_links or self.args.hard_links:
                gen_links_dir = scan_action.generate_links()
            if self.args.print_duplicates:
                scan_action.print_duplicates()
            elif self.args.isolate:
                isolation_path = scan_action.isolate_duplicates()
                if isolation_path:
                    remove_empty_dirs(path=isolation_path, remove_base_dir=False, verbose=self.args.verbose,
                                      re_print=False)
                    p('\nPlease check: %s' % isolation_path)
                    p('Note that: The above location will be gone if anything happens to')
                    p('the operating system such as restart, power-off, crash... and so on')
            elif self.args.remove:
                scan_action.remove_duplicates_with_prompt()
            elif self.args.autoremove:
                scan_action.remove_duplicates_auto()

            p()
            pl(MAX_LINE_COLUMNS)
            p('   Total Files : %s' % len(scan_data))
            p('    Duplicates : %s' % dups_data.duplicates)
            p('          Sets : %s' % dups_data.sets)
            p('     Occupying : %s' % bytes_to_readable_units(dups_data.size))
            p('Hash Signature : %s' % self.args.hashtype)
            pl(MAX_LINE_COLUMNS)

            if (self.args.soft_links or self.args.hard_links) and gen_links_dir:
                p('\nPlease check: %s\n' % gen_links_dir)

        return

    def __action_precopy(self) -> None:
        """ Scan both given directories, and group the unique files in first directory. """

        unique_action = DuGuPreCopyAction(args=self.args)
        unique_action.start()

        src_data, _, unique_data = unique_action.result()

        p()
        pl(MAX_LINE_COLUMNS)
        p('  Total Found Files: %d' % len(src_data))
        p(' Found Unique Files: %d' % len(unique_data.files_list))
        p(' Total Copied Files: %d' % (len(unique_data.files_list) - len(unique_action.not_copied_files)))
        p(' Avoided Duplicates: %d' % (len(src_data) - len(unique_data.files_list)))
        p('        Saved Space: %s' % bytes_to_readable_units(src_data.size - unique_data.files_size))
        pl(MAX_LINE_COLUMNS)
        p('\nPlease Check: %s\n' % unique_action.unique_path)

        # scan the unique-path, if needed:
        if self.args.print_duplicates or self.args.soft_links or self.args.hard_links \
                or self.args.isolate or self.args.remove or self.args.autoremove:
            p('\nScanning: %s\n' % unique_action.unique_path)
            delattr(self.args, 'DIRS')
            setattr(self.args, 'DIR', unique_action.unique_path)
            self.__action_scan()

        return


# ----------------------------------------------------------------------


if __name__ == '__main__':
    p('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
