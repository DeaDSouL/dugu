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
from os import (
    path as os_path,
    symlink as os_symlink,
    link as os_link,
)
from shutil import (
    disk_usage as shutil_disk_usage,
    rmtree,
)

# Third party imports

# Local application imports
from dugu.core import (
    DuGuDuplicatesCore,
    DuGuUniqueCore,
)
from dugu.constants import (
    DUGU_BASE_PATH,
    DUGU_ISOLATION_PATH,
    DUGU_SOFT_LINKS_PATH,
    DUGU_HARD_LINKS_PATH,
    MAX_LINE_COLUMNS,
)
from dugu.utils import (
    hash_string,
    mkdir,
    auto_rename_file,
    bytes_to_readable_units,
    build_path,
    copy_directory_structures,
    move_files_to_replicant_except,
    remove_files_except,
    iteritems,
    _exit,
)
from dugu.app_input import (
    prompt,
    args_namespace,
)
from dugu.app_output import (
    _print as p,
    _print_fixed as pf,
    reprint_fixed as rpf,
    log as log,
    print_line as pl,
    waiting_indicator,
)


# ----------------------------------------------------------------------

class DuGuScanAction(DuGuDuplicatesCore):
    """ The main scan action class """

    # ------------------------------
    #        SPECIAL METHODS
    # ------------------------------

    def __init__(self, args=args_namespace()) -> None:
        """ Preparing stuff for the scanning action. """

        super(DuGuScanAction, self).__init__(args=args)

    # ------------------------------
    #             PUBLIC
    # ------------------------------

    # ----------( FLAGS )-----------

    def print_duplicates(self) -> None:
        """Prints all duplicates sorted by their sets."""

        p()
        i1 = 0
        for sig, files in iteritems(self._dups_result.duplicated_files):
            i1 += 1
            p('%s) Signature: %s :' % (i1, sig))
            i2 = 0
            for file in files:
                i2 += 1
                p('        %s) %s' % (i2, file))
            p()

    def isolate_duplicates(self) -> bool or str:
        """ Isolates all duplicates to the 'isolation path', then return the 'isolation path'. """

        isolate_sig = hash_string(os_path.abspath(self._cwd), 'md5')
        mkdir(DUGU_ISOLATION_PATH, verbose=self._args.verbose, check=True)
        isolate_path = build_path(dirs='%s_%s' % (isolate_sig, self._args.hashtype), prefix_path=DUGU_ISOLATION_PATH)

        # Make sure we have enough disk space before the isolation process.
        disk_available_space = shutil_disk_usage(isolate_path).free
        disk_required_space = self._dups_result.size + (100 * 1024 * 1024)  # plus 100MiB (to be safe)
        if disk_available_space <= disk_required_space:
            log(msg='Canceling the isolation process. The available disk space in "%s" is (%s) which is less than the '
                    'minimum required space (%s).!' % (DUGU_BASE_PATH,
                                                       bytes_to_readable_units(disk_available_space),
                                                       bytes_to_readable_units(disk_required_space)),
                verbose=self._args.verbose, re_print=False, lvl=1)
            return False

        # Since this is isolation, we need to make sure we don't remove anything without the user's permission
        i = 0
        tmp_dir = isolate_path[:]
        while os_path.isdir(isolate_path):
            i += 1
            isolate_path = '%s_%s' % (tmp_dir, i)

        copy_directory_structures(src=self._cwd, dst=isolate_path, copy_symlinks=not self._args.follow_symlinks,
                                  verbose=self._args.verbose, re_print=True)
        p('Copying Dir Structure..Done \r')

        i = 0
        for sig, files in iteritems(self._dups_result.duplicated_files):
            i += 1
            if i > 1:
                pl(60)
            p('[%s/%s] Signature: %s :' % (i, self._dups_result.sets, sig))
            if not os_path.exists(files[0]) or not os_path.isfile(files[0]) or os_path.islink(files[0]):
                p('Ignoring this set.')
                continue

            # make sure the file: files[keep_key] exists
            keep_key = 0
            while not os_path.exists(files[keep_key]) and keep_key in range(len(files)):
                keep_key += 1

            # skip this (sig, files), and go to next ones
            if keep_key >= len(files):
                log(msg='Could not find any existed file to keep. Ignoring this set: "%s".!!' % sig,
                    verbose=self._args.verbose, re_print=False, lvl=1)
                continue

            move_files_to_replicant_except(keep=keep_key, files=files, start_dir=self._cwd, dst_dir=isolate_path,
                                           verbose=self._args.verbose, re_print=False)

        pl(60)
        return isolate_path

    def remove_duplicates_with_prompt(self):
        i = 0
        for sig, files in iteritems(self._dups_result.duplicated_files):
            i += 1
            if i > 1:
                pl(60)
            p('[%s/%s] Signature: %s :' % (i, self._dups_result.sets, sig))
            keys = len(files)
            for key, file in enumerate(files):
                p('        [%s] %s' % (key + 1, file))

            options = '1-%s, all or exit: ' % keys
            choices = tuple(range(1, keys + 1)) + ('all', 'exit')
            answer = prompt(msgs=('Which file would you like to preserve?', options), choices=choices,
                            verbose=self._args.verbose, re_print=True)
            p('')

            if answer == 'all':
                p('Preserving all files in this set.')
                for key, file in enumerate(files):
                    p('    [+] [%s] %s' % (key + 1, file))
            elif answer == 'exit':
                p('Exiting,...')
                return False
            elif type(answer) == int:
                selected_file = files[answer - 1]
                selected_key = answer - 1
                if not os_path.exists(selected_file):
                    p('The selected file to preserve, is somehow not available!')
                    p('Ignoring this set.')
                    continue
                if os_path.islink(selected_file):
                    p('The selected file to preserve, is a link.')
                    p('This might cause loosing the actual file.')
                    if prompt(msgs='Are you sure you want to proceed ? (YES/NO): ', choices=('YES', 'NO'),
                              verbose=self._args.verbose, re_print=True) == 'NO':
                        p('Ignoring this set.')
                        continue
                remove_files_except(keep=selected_key, files=files, verbose=self._args.verbose, re_print=True)
            else:
                log(msg='Unknown answer!! Skipping this set.', verbose=self._args.verbose, re_print=True, lvl=1)
                continue

            if i == self._dups_result.sets:
                pl(60)

    def remove_duplicates_auto(self):
        i = 0
        for sig, files in iteritems(self._dups_result.duplicated_files):
            i += 1
            if i > 1:
                pl(60)
            p('[%s/%s] Signature: %s :' % (i, self._dups_result.sets, sig))
            if not os_path.exists(files[0]) or not os_path.isfile(files[0]) or os_path.islink(files[0]):
                p('Ignoring this set.')
                continue
            remove_files_except(keep=0, files=files, verbose=self._args.verbose, re_print=True)
            if i == self._dups_result.sets:
                pl(60)

    def generate_links(self) -> bool or str:
        if self._dups_result.duplicates > 0 and self._args.soft_links:
            links_path = DUGU_SOFT_LINKS_PATH
            links_func = os_symlink
            links_text = 'SoftLinks'
        elif self._dups_result.duplicates > 0 and self._args.hard_links:
            links_path = DUGU_HARD_LINKS_PATH
            links_func = os_link
            links_text = 'HardLinks'
        else:
            return False

        # (cwd-md5-sig)_(md5|sha1|sha256|sha512)/
        rep_dir_sig = hash_string(self._cwd, 'md5')

        sub_links_path = build_path('%s_%s' % (rep_dir_sig, self._args.hashtype), prefix_path=links_path)

        # on force, or _init_scan() is called: remove generated links dir
        if self._need_scan and os_path.exists(sub_links_path):
            pf('Removing Old %s' % links_text, status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
            rmtree(sub_links_path)

        if not os_path.exists(sub_links_path):
            if mkdir(links_path, verbose=self._args.verbose, check=True):
                pf('Creating %s Dir' % links_text, status='Done', suffix='\r', suffix_space=True,
                   max_cols=MAX_LINE_COLUMNS)
            else:
                log(msg='Could not make directory: "%s"..' % links_path, verbose=self._args.verbose,
                    re_print=False, lvl=0)
                return False

            for sig, files in iteritems(self._dups_result.duplicated_files):
                sub_rep_dir = os_path.join(sub_links_path, sig)
                log(msg='Creating new set directory: %s' % sub_rep_dir, verbose=self._args.verbose)
                if not mkdir(sub_rep_dir, verbose=False, check=False):
                    log(msg='Could not make directory: "%s"..' % sub_rep_dir, verbose=self._args.verbose, lvl=0)
                    return False
                for file in files:
                    rpf(msg='Generating %s.' % links_text, status='%s' % waiting_indicator(),
                        suffix=' \r', max_cols=MAX_LINE_COLUMNS)
                    dst_link = auto_rename_file(os_path.join(sub_rep_dir, os_path.basename(file)))
                    try:
                        links_func(file, dst_link)
                    except OSError as _:
                        log(msg='Failed linking: "%s" to: "%s"' % (dst_link, file), verbose=self._args.verbose, lvl=1)
            pf('Generating %s' % links_text, status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
        else:
            pf('Loading %s' % links_text, status='Done', suffix='\r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)

        return sub_links_path

    # ------------------------------
    #            PRIVATE
    # ------------------------------

    # ------------------------------
    #             HOOKS
    # ------------------------------

    # ------------------------------
    #           UN-NEEDED
    # ------------------------------


# ----------------------------------------------------------------------


class DuGuPreCopyAction(DuGuUniqueCore):
    def __init__(self, args=args_namespace()):
        super(DuGuPreCopyAction, self).__init__(args=args)


# ----------------------------------------------------------------------


if __name__ == '__main__':
    p('This file is part of DuGu package.')
    _exit('And is not meant to run directly.')
