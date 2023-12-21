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
from __future__ import absolute_import, print_function
from sys import stdout as sys_stdout

# Third party imports

# Local application imports
from dugu.decorators import static_vars
from dugu.version import ver


# ----------------------------------------------------------------------


def _print(*args, **kwargs) -> None:
    """ print() wrapper. """
    # print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)
    print(*args, **kwargs)


def _print_fixed(msg='', status='' or 'Done' or 'Fail', max_cols=27, suffix='', suffix_space=False):
    return fixed_print(msg=msg, status=status, max_cols=max_cols,
                       suffix=suffix, suffix_space=suffix_space, func=_print)


def reprint(msg='') -> None:
    """ Re-prints on the same line. """
    if ver.py.short >= 3.3:  # 'flush=true' is a feature started from Python 3.3
        _print('\r%s' % msg, end='', flush=True),
    else:
        _print('\r%s' % msg, end=''),
        sys_stdout.flush()


def reprint_fixed(msg='', status='' or 'Done' or 'Fail', max_cols=27, suffix='', suffix_space=False):
    return fixed_print(msg=msg, status=status, max_cols=max_cols,
                       suffix=suffix, suffix_space=suffix_space, func=reprint)


def fixed_print(msg='', status='' or 'Done' or 'Fail', max_cols=27,
                suffix='', suffix_space=False, func=_print or reprint):
    length = len(msg + status)

    if length >= max_cols:
        msg = msg[:max_cols - 3 - len(status)]
        dots = '.' * 3
    else:
        dots = '.' * (max_cols - length)

    if suffix_space:
        # suffix = ' ' * (max_cols + 5) + suffix
        # TODO: or instead of max_cols, make it fixed to 30?
        #       or find the max cols in terminal and use the diff?
        suffix = ' ' * max_cols + suffix

    return func('%s%s%s%s' % (msg, dots, status, suffix))


# ----------------------------------------------------------------------


def clear_prev_line(length=80) -> None:
    """ Prints spaces to overwrite last line. """

    reprint(' ' * length)


def print_line(length=60) -> None:
    """ Prints line. """

    _print('-' * length)


# ----------------------------------------------------------------------


@static_vars(level=('[ ERROR ]', '[WARNING]', '[ INFO  ]', '[ DEBUG ]'))
def log(msg='', verbose=False, re_print=False, lvl=2 or range(4)) -> None:
    """ Print app messages.
    msg:        string  message
    verbose     bool    False|True
    re_print    bool    False|True
    lvl:        int     0: ERROR, 1: WARNING, 2:INFO, 3:DEBUG """

    # if 'level' not in log.__dict__:
    #     log.level = ('[ ERROR ]', '[WARNING]', '[ INFO  ]', '[ DEBUG ]')

    if verbose:
        if re_print:
            clear_prev_line(80)
            _print('\r%s: %s' % (log.level[lvl], msg))
        else:
            _print('%s: %s' % (log.level[lvl], msg))

    return


# ----------------------------------------------------------------------


@static_vars(i=0, symbols=('\\', '|', '/', '--'))
def waiting_indicator() -> str:
    if waiting_indicator.i >= len(waiting_indicator.symbols):
        waiting_indicator.i = 0
    waiting_indicator.i += 1
    return waiting_indicator.symbols[waiting_indicator.i-1]


# ----------------------------------------------------------------------


if __name__ == '__main__':
    _print('This file is part of DuGu package.')
    exit('And is not meant to run directly.')
