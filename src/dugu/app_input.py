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
from os import getcwd as os_getcwd
import argparse

# Third party imports

# Local application imports
from dugu.constants import (
    DUGU_UNIQUE_FILES_DIR,
)
from dugu.app_output import (
    _print as p,
    log as log,
)
from dugu.version import ver


# ----------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """ Initiate argparse and return Obj.parse_args() """

    parser = argparse.ArgumentParser(prog='DuGu',
                                     description='Duplicated files manager tool. Version: %s' % ver.dugu.full)
    # --------------------------------------------------------------------------------------------------------------
    parser.add_argument('-V', '--version', action='store_true',
                        help='Show DuGu version.')
    # --------------------------------------------------------------------------------------------------------------
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increase output verbosity. (not fully implemented yet)')
    # --------------------------------------------------------------------------------------------------------------
    parser.add_argument('-s', '--symlinks', action='store_true', default=False,
                        help='Follow symbolic links that point to files, even if they are located out of the '
                             'target-directory. (not recommended)')
    parser.add_argument('-S', '--follow-symlinks', dest='follow_symlinks', action='store_true', default=False,
                        help='Follow symbolic links that point to directories. even if they are located out of the '
                             'target-directory. (not recommended)')
    # --------------------------------------------------------------------------------------------------------------
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Ignoring the generated cache. And re-generate a new one.')
    # --------------------------------------------------------------------------------------------------------------
    parser.add_argument('-t', '--hashtype', type=str, default='md5',
                        choices=['md5', 'sha1', 'sha256', 'sha512'],
                        help='The algorithm to be used in scanning files. (default: md5)')
    # --------------------------------------------------------------------------------------------------------------
    group = parser.add_mutually_exclusive_group()
    # --------------------------------------------------------------------------------------------------------------
    group.add_argument('-p', '--print_duplicates', action='store_true', default=False,
                       help='''will print all the duplicated files categorized by their sets. Please note that, this 
                       argument is meant to only work with argument "scan"; So if it is being called with argument 
                       "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected 
                       optional arguments with "scan" to the produced directory "%s".''' % DUGU_UNIQUE_FILES_DIR)
    # --------------------------------------------------------------------------------------------------------------
    group.add_argument('-l', '--soft-links', dest='soft_links', action='store_true', default=False,
                       help='''will generate a folder that has soft-links to all of the duplicated files categorized by 
                       their sets. Please note that, this argument is meant to only work with argument "scan"; So if it 
                       is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will 
                       execute the same selected optional arguments with "scan" to the produced directory "%s".'''
                            % DUGU_UNIQUE_FILES_DIR)
    group.add_argument('-L', '--hard-links', dest='hard_links', action='store_true', default=False,
                       help='''will generate a folder that has hard-links to all of the duplicated files categorized by 
                       their sets. Please note that, this argument is meant to only work with argument "scan"; So if it 
                       is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will 
                       execute the same selected optional arguments with "scan" to the produced directory "%s".'''
                            % DUGU_UNIQUE_FILES_DIR)
    # --------------------------------------------------------------------------------------------------------------
    group.add_argument('-i', '--isolate', action='store_true', default=False,
                       help='''will move the duplicated files to a folder called "isolate" under the temporary folder in 
                       your operating-system. Please note that, this argument is meant to only work with argument 
                       "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to 
                       "dir1", then will execute the same selected optional arguments with "scan" to the produced 
                       directory "%s".''' % DUGU_UNIQUE_FILES_DIR)
    # --------------------------------------------------------------------------------------------------------------
    group.add_argument('-r', '--remove', action='store_true', default=False,
                       help='''will prompt user for files to preserve and remove all others; important: under particular 
                       circumstances, data may be lost when using this option together with -s or --symlinks. Please 
                       note that, this argument is meant to only work with argument "scan"; So if it is being called 
                       with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the 
                       same selected optional arguments with "scan" to the produced directory "%s".'''
                            % DUGU_UNIQUE_FILES_DIR)
    group.add_argument('-R', '--autoremove', action='store_true', default=False,
                       help='''will preserve the first file in each set of duplicates and remove the rest without 
                       prompting the user. Please note that, this argument is meant to only work with argument "scan"; 
                       So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", 
                       then will execute the same selected optional arguments with "scan" to the produced directory 
                       "%s".''' % DUGU_UNIQUE_FILES_DIR)
    # --------------------------------------------------------------------------------------------------------------
    subparsers = parser.add_subparsers(help='Main Commands', dest='cmd')
    # --------------------------------------------------------------------------------------------------------------
    parser_scan = subparsers.add_parser('scan',
                                        help='''(ex: scan "path/to/dir") To preform a normal scan for the duplicated 
                                        files, followed by the path of the directory.''')
    parser_scan.add_argument('DIR', type=str, nargs='?', action='store',
                             default=os_getcwd(), help='The path of the directory to scan.')
    # --------------------------------------------------------------------------------------------------------------
    parser_precopy = subparsers.add_parser('precopy',
                                           help='''(ex: precopy "path/to/dir1" "path/to/dir2"): To exclude all the files 
                                           in "dir1" that already in "dir2", and put the unique files in a folder called
                                           "%s" inside "dir1" with the same structure of "dir1".'''
                                                % DUGU_UNIQUE_FILES_DIR)
    parser_precopy.add_argument('DIRS', type=str, nargs=2, action='store',
                                help='Expects 2 dirs: DIR_FROM and DIR_TO.')
    # --------------------------------------------------------------------------------------------------------------

    return parser.parse_args()


# ----------------------------------------------------------------------


def args_namespace():
    return argparse.Namespace


# ----------------------------------------------------------------------


def prompt(msgs: (str, tuple), choices: tuple, invalid: str = 'Invalid answer!',
           verbose: bool = False, re_print: bool = True) -> str or int or float:
    """Keeps asking user a question, until one of the given choices is received.

        msgs: Can either be a single message, or a tuple() of messages.
        choices: Contains all allowed choices.
        invalid: Is the message that we print to user, when an invalid answer is received."""

    answer = None

    # extract msgs
    msg = msgs if type(msgs) == str else ''
    if type(msgs) == tuple:
        for m in msgs:
            msg = '%s\n%s' % (msg, m)

    # remember the integer & float choices
    choices_int = tuple(str(choice) for choice in choices if type(choice) == int)
    choices_flt = tuple(str(choice) for choice in choices if type(choice) == float)
    choices_str = tuple(choice for choice in choices if type(choice) == str)

    # convert all choices type to string
    choices = choices_int + choices_flt + choices_str

    # keep throwing prompt, till a valid answer is received
    while answer not in choices:
        if answer is not None:
            p('')
            p(invalid)
            p('')
        answer = input(msg)

    # convert the answer type to what it's meant to be
    if choices_flt and answer in choices_flt:
        try:
            answer = float(answer)
        except ValueError as _:
            log(msg='Could not make a float value from "%s".!!' % answer, verbose=verbose, re_print=re_print, lvl=1)
    elif choices_int and answer in choices_int:
        try:
            answer = int(answer)
        except ValueError as _:
            log(msg='Could not make an integer value from "%s".!!' % answer, verbose=verbose, re_print=re_print, lvl=1)

    return answer


# ----------------------------------------------------------------------


if __name__ == '__main__':
    print('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
