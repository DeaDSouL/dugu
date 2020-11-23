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
from multiprocessing import cpu_count
from sys import exit as sys_exit
from contextlib import suppress
from os import (
    path as os_path,
    walk as os_walk,
    makedirs as os_mkdir,
    rmdir as os_rmdir,
    listdir as os_listdir,
    access as os_access,
    remove as os_remove,
    R_OK,
    W_OK,
)
from tempfile import mkdtemp
from shutil import (
    move as mv,
    copytree,
    copy2,
    SameFileError as shutil_SameFileError,
    Error as shutil_Error
)
from hashlib import (
    md5 as hashlib_md5,
    sha1 as hashlib_sha1,
    sha256 as hashlib_sha256,
    sha512 as hashlib_sha512,
)

# Third party imports

# Local application imports
from dugu.constants import (
    MAX_LINE_COLUMNS,
    DEFAULT_TMP_PATH,
    DUGU_BASE_PATH,
)
from dugu.app_output import (
    _print as p,
    _print_fixed as pf,
    reprint_fixed as rpf,
    log as log,
    waiting_indicator,
)
from dugu.version import ver


# ----------------------------------------------------------------------


# ------------------------------
#         H A S H I N G
# ------------------------------


def hash_file_contents(filename, hash_type='md5') -> str:
    """Returns the md5, sha1, sha256 or sha512 hash of the given file"""
    if hash_type == 'sha1':
        hash_sum = hashlib_sha1()
    elif hash_type == 'sha256':
        hash_sum = hashlib_sha256()
    elif hash_type == 'sha512':
        hash_sum = hashlib_sha512()
    else:
        hash_sum = hashlib_md5()

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_sum.update(chunk)

    return hash_sum.hexdigest()
    # return hash_sum.digest()


def hash_string(string='', hash_type='md5'):
    """Returns the md5, sha1, sha256 or sha512 hash of the given string"""
    if hash_type == 'sha1':
        ret = hashlib_sha1(str(string).encode('utf-8')).hexdigest()
    elif hash_type == 'sha256':
        ret = hashlib_sha256(str(string).encode('utf-8')).hexdigest()
    elif hash_type == 'sha512':
        ret = hashlib_sha512(str(string).encode('utf-8')).hexdigest()
    else:
        ret = hashlib_md5(str(string).encode('utf-8')).hexdigest()

    return ret


# ------------------------------
#      FILES & DIRECTORIES
# ------------------------------


def build_path(dirs='' or int or float or tuple or list, prefix_path=DUGU_BASE_PATH) -> str:
    """ Return a joined one or more paths as string. """

    ret = prefix_path
    dirs_type = type(dirs)
    if dirs and dirs_type in (tuple, list):
        for d in dirs:
            ret = os_path.join(ret, d)
    elif dirs and dirs_type == str:
        ret = os_path.join(ret, dirs)
    elif dirs and dirs_type in (int, float):
        ret = os_path.join(ret, str(dirs))

    return ret


def bytes_to_readable_units(num, suffix='B') -> str:
    """ Return a human readable units out of given bytes. """

    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def path_is(paths: str or tuple or list, checks='erw', verbose=False, re_print=False, log_lvl=1):
    """ Return True if a given path meets all checks, otherwise False..

        paths: str or tuple or list. The path(s) of a file or a directory.
        checks: (str) One or more of the following options:
                    'e' -> path must be existed.
                    'E' -> path must be existed even if it's a broken symlink.
                    'l' -> path must be a link.
                    'f' -> path must be a file.
                    'd' -> path must be a directory.
                    'r' -> path must be readable.
                    'w' -> path must be writable.
        verbose: (bool) Whether or not enable verbosity.
        re_print: (bool) Whether or not to re-print log on the same line.
        log_lvl: (int) 0..3."""

    if not paths:
        log(msg="'%s': is empty." % paths, verbose=verbose, re_print=False, lvl=1)
        return False
    if type(paths) is str:
        paths = [paths]
    if type(paths) not in (tuple, list):
        log(msg="'%s': has invalid type." % paths, verbose=verbose, re_print=False, lvl=1)
        return False
    if type(checks) is not str:
        checks = 'erw'
    # TODO: maybe we don't need the following 3 if-statements??
    if type(verbose) is not bool:
        verbose = False
    if type(re_print) is not bool:
        re_print = False
    if type(log_lvl) is not int or 3 < log_lvl < 0:
        log_lvl = 1

    for path in paths:
        if 'e' in checks and not os_path.exists(path):
            log(msg="'%s': does not exist." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'E' in checks and not os_path.exists(path) and not os_path.islink(path):
            log(msg="'%s': does not exist." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'l' in checks and not os_path.islink(path):
            log(msg="'%s': is not a link." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'f' in checks and not os_path.isfile(path):
            log(msg="'%s': is not a file." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'd' in checks and not os_path.isdir(path):
            log(msg="'%s': is not a directory." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'r' in checks and not os_access(path, R_OK):
            log(msg="'%s': is not readable." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False
        elif 'w' in checks and not os_access(path, W_OK):
            log(msg="'%s': is not writable." % path, verbose=verbose, re_print=re_print, lvl=log_lvl)
            return False

    return True


# ------------------------------
#          DIRECTORIES
# ------------------------------


def auto_rename_dir(dir_path=None) -> str:
    """ Return a suggested name of a given existed directory.
        If it doesn't exist, return the same given name. """

    if not dir_path or not os_path.exists(dir_path):
        return dir_path

    new_dir_path = dir_path
    dir_name, basename = os_path.split(dir_path)

    i = 0
    while os_path.exists(new_dir_path):
        i += 1
        new_dir_path = os_path.join(dir_name, '%s_%d' % (basename, i))

    return new_dir_path


def mkdir(_dir=None, verbose=False, check=True) -> bool:
    """ Create a directory if it doesn't exist. And optionally, check the existing directory whether it's or not a
        readable and writable directory. """

    if not path_is(paths=_dir, checks='E'):
        log(msg='Creating directory: "%s"' % _dir, verbose=verbose, re_print=False, lvl=2)
        try:
            os_mkdir(_dir)
        except OSError as e:  # e.errno  &  e.strerror
            log(msg="Failed while trying to create directory: '%s'! Because: '%d: %s'." % (_dir, e.errno, e.strerror),
                verbose=verbose, lvl=1)
            return False

    if check:
        log(msg='Testing directory: "%s"' % _dir, verbose=verbose, re_print=False, lvl=2)
        return path_is(paths=_dir, checks='Edrw', verbose=verbose)

    return True


def mktemp_dir(_dir=None, verbose=False) -> str:
    """ Return the created temp dir. """
    dir_type = type(_dir)
    if _dir and dir_type in (str, int, float):
        _dir = str(_dir) if dir_type in (int, float) else _dir
        dst = build_path(_dir, DEFAULT_TMP_PATH)
        if not os_path.exists(dst):
            ret = mkdtemp()
            try:
                mv(ret, dst)
            except shutil_Error as _:
                log("Couldn't move '%s' to '%s'!" % (ret, dst), verbose=verbose, lvl=1)
            else:
                ret = dst
        else:
            def _mktemp_dir_error(msg='') -> str:
                log(msg="Custom tmp name failed. Because it's already existed yet %s" % msg, verbose=verbose, lvl=1)
                return mkdtemp()

            if not os_path.isdir(dst):
                ret = _mktemp_dir_error("it's not a directory.")
            elif not os_access(dst, R_OK):
                ret = _mktemp_dir_error("it's not readable.")
            elif not os_access(dst, W_OK):
                ret = _mktemp_dir_error("it's not writable.")
            else:
                ret = dst
    else:
        ret = mkdtemp()
    return ret


def copy_directory_structures(src='', dst='', copy_symlinks=False, verbose=False, re_print=True) -> bool:
    """ Recursively copy an entire directory tree rooted at 'src' to a directory named 'dst' without the files.

        'src': should be an existed directory.
        'dst': should not be existed.
        copy_symlinks: If it's set to True, it will copy the symlinks found in 'src' to 'dst'.
        If false or omitted, it will copy the linked directories.
        verbose: whether or not to show extra information.
        re_print: whether or not to print on the previous line."""

    if not os_path.isdir(src):
        log(msg='Source path "%s" is not a directory.!!' % src, verbose=verbose, re_print=re_print, lvl=1)
        return False
    elif dst and os_path.exists(dst):
        log(msg='Destination path "%s" exists.!!' % dst, verbose=verbose, re_print=re_print, lvl=1)
        return False

    copytree(src, dst, symlinks=copy_symlinks, ignore=ignore_all_but_dirs)
    return True


def ignore_all_but_dirs(folder, names) -> set:
    """ Return a collection of everything except directories in a given path and its contents. """

    return set(n for n in names if not os_path.isdir(os_path.join(folder, n)))


def remove_empty_dirs(path=None, remove_base_dir=False, verbose=False, re_print=True) -> None:
    """ Recursively remove all empty directories in a given path. (Optionally including its base). """

    if os_path.isdir(path):
        for content in os_listdir(path):
            content = os_path.join(path, content)
            if os_path.isdir(content):
                log(msg='Checking "%s".' % content, verbose=verbose, re_print=re_print, lvl=3)
                remove_empty_dirs(path=content, remove_base_dir=True, verbose=verbose, re_print=re_print)
        if not os_listdir(path) and remove_base_dir:
            log(msg='Removing "%s".' % path, verbose=verbose, re_print=re_print, lvl=2)
            if ver.py.short >= 3.4:
                with suppress(FileNotFoundError, OSError):
                    os_rmdir(path)
            else:
                log(msg='Removing "%s".' % path, verbose=verbose, re_print=re_print, lvl=2)
                try:
                    os_rmdir(path)
                except (FileNotFoundError, OSError) as _:
                    log(msg='Could not remove "%s".!!' % path, verbose=verbose, re_print=re_print, lvl=1)


def get_dir_size(dir_path=None, follow_links=False, which=None, show_progress=False,
                 verbose=False, re_print=True) -> int:
    """ Calculate and return the total files size in a given directory's path. """

    total_size = 0
    if path_is(paths=dir_path, checks='edr', verbose=verbose, re_print=re_print):
        if show_progress:
            if which and which.upper() in ('SRC', 'DST'):
                which = '%s ' % which.upper()
            else:
                which = ''

            for path, _, files in os_walk(dir_path, followlinks=follow_links):
                rpf(msg='Calculating %sSize' % which, status='%s' % waiting_indicator(),
                    suffix=' \r', max_cols=MAX_LINE_COLUMNS)
                if path_is(paths=path, checks='er', verbose=verbose, re_print=re_print):
                    for f in files:
                        fp = os_path.join(path, f)
                        if not os_path.islink(fp):
                            total_size += os_path.getsize(fp)
                else:
                    log(msg='Skipping directory: "%s" because it is not readable!' % path,
                        verbose=verbose, re_print=re_print, lvl=1)
            pf('Calculating %sSize' % which, status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
        else:
            total_size = sum((os_path.getsize(os_path.join(path, f)) for path, _, files in
                              os_walk(dir_path, followlinks=follow_links)
                              if path_is(paths=path, checks='er', verbose=verbose, re_print=re_print) for f in files
                              if not os_path.islink(os_path.join(path, f))))

    return total_size


# ------------------------------
#            FILES
# ------------------------------


def auto_rename_file(file_path=None) -> str:
    """ Return a suggested name of a given existed file.
        If it doesn't exist, return the same given name. """

    if not file_path or not os_path.exists(file_path):
        return file_path

    new_file = file_path
    dir_name, basename = os_path.split(file_path)
    name, ext = os_path.splitext(basename)

    i = 0
    while os_path.exists(new_file):
        i += 1
        new_file = os_path.join(dir_name, '%s_%d%s' % (name, i, ext))

    return new_file


def count_files(path=None, which=None, follow_links=False, show_progress=False, verbose=False) -> int:
    """ Return the count of files that have been recursively found in a given path. """

    total_files = 0
    if not path_is(paths=path, checks='ed', verbose=verbose, log_lvl=3):
        return total_files
    elif show_progress:
        msg = 'Counting %sFiles' % which.upper() if which and which.upper() in ('SRC', 'DST') else 'Counting Files'

        for path, _, filenames in os_walk(path, followlinks=follow_links):
            total_files += len(filenames)
            rpf(msg=msg, status=' %s' % waiting_indicator(), suffix=' \r', max_cols=MAX_LINE_COLUMNS)
        pf(msg=msg, status='Done', suffix=' \r', suffix_space=True, max_cols=MAX_LINE_COLUMNS)
    else:
        # same as the following, (will count links AND sockets). but won't be able to show the progress until it's done
        total_files = sum((len(f) for _, _, f in os_walk(path, followlinks=follow_links)))

    return total_files


def find_files_recursively(path=None, which=None, follow_links=False, show_progress=False, verbose=False) -> list:
    """ Return a list of files that have been found recursively in a given path. """

    files = []
    if not path_is(paths=path, checks='ed', verbose=verbose, log_lvl=3):
        return files
    elif show_progress:
        msg = 'Finding %s Files' % which.upper() if which and which.upper() in ('SRC', 'DST') else 'Finding Files'

        for _path, _, filenames in os_walk(path, followlinks=follow_links):
            files += [os_path.join(_path, f) for f in iter(filenames)]
            rpf(msg=msg, status=' %s' % waiting_indicator(), suffix=' \r', max_cols=MAX_LINE_COLUMNS)

        pf(msg=msg, status='Done', suffix=' \r', max_cols=MAX_LINE_COLUMNS)

    else:
        # same as the following, (will count links AND sockets). but won't be able to show the progress until it's done
        files = [os_path.join(_p, f) for _p, _, ff in os_walk(path, followlinks=follow_links) for f in iter(ff)]

    return files

# ----------------------------------------------------------------------


def copy_file_to_replicant(file=None, start_dir=None, dst_dir=None, follow_symlinks=False,
                           verbose=False, re_print=True) -> bool:
    if not file or not path_is(paths=file, checks='Efr', verbose=False, re_print=re_print):
        log(msg='"%s": is not an existed readable file!' % file, verbose=verbose, re_print=re_print, lvl=1)
        return False

    if not start_dir or not path_is(paths=start_dir, checks='Edr', verbose=False, re_print=re_print):
        log(msg='"%s": is not an existed readable directory!' % start_dir, verbose=verbose, re_print=re_print, lvl=1)
        return False

    sub_path = os_path.relpath(file, start_dir)
    new_file = os_path.join(dst_dir, sub_path)
    new_dir = os_path.dirname(new_file)

    if not new_dir or not path_is(paths=new_dir, checks='Edr', verbose=False, re_print=re_print):
        log(msg='"%s": is not an existed readable directory!' % new_dir, verbose=verbose, re_print=re_print, lvl=1)
        return False

    try:
        copy2(src=file, dst=new_file, follow_symlinks=follow_symlinks)
    except shutil_SameFileError:
        log(msg='Source and destination are identical: "%s"!' % file, verbose=verbose, re_print=re_print, lvl=1)
        return False
    except PermissionError:
        log(msg='Permission denied to copy "%s" to "%s"!' % (file, new_file),
            verbose=verbose, re_print=re_print, lvl=1)
        return False
    except (OSError, IOError, shutil_Error):
        log(msg='Could not copy "%s" to "%s"!' % (file, new_file), verbose=verbose, re_print=re_print, lvl=1)
        return False
    return True


def move_files_to_replicant_except(keep=0 or '', files=None, start_dir=None, dst_dir=None, verbose=False,
                                   re_print=True) -> bool:
    """ Moves all files, except the one with the given key, to 'dst_dir' followed by the same sub-folders they're in.

        keep: Could be an integer represents the element key in 'files', or string as one of the 'files' elements value.
        files: Should be a list, that holds the files which need to be moved.
        start_dir: holds the starting point where any sub-folder holds the file, should be considered as the sub-folders
        in the 'dst_dir'. """

    if not files or (not keep and keep != 0) or type(files) != list or type(keep) not in (int, str) \
            or not start_dir or not os_path.isdir(start_dir) or not dst_dir or not os_path.isdir(dst_dir) \
            or (type(keep) == int and
                (not os_path.exists(files[keep]) or keep not in range(len(files)))) \
            or (type(keep) == str and
                (not os_path.exists(keep) or keep not in files)):
        log(msg='Invalid one of the passed arguments (keep|files|start_dir) !',
            verbose=verbose, re_print=re_print, lvl=1)
        return False

    ret = True

    for k, f in enumerate(files):
        if keep in (k, f):
            p('    [+] [%s] %s' % (k + 1, f))
        else:
            if os_path.exists(f):
                sub_path = os_path.relpath(f, start_dir)
                new_file = os_path.join(dst_dir, sub_path)
                if move_file(src=f, dst=new_file, rename_if_dst_exists=True, verbose=verbose, re_print=re_print):
                    p('    [-] [%s] %s' % (k + 1, f))
                else:
                    log(msg='Could not move "%s" to "%s"!' % (f, new_file), verbose=verbose, re_print=re_print, lvl=1)
                    ret = False
            else:
                log(msg='Somehow the file "%s", does not exist when we tried to move it!' % f, verbose=verbose,
                    re_print=re_print, lvl=1)
                ret = False

    return ret


def move_file(src=None, dst=None, rename_if_dst_exists=False, verbose=False, re_print=True) -> bool:
    """ Move the given file to the destination and optionally rename it on existence. """

    dst_dir_name = os_path.dirname(dst)
    if os_path.exists(src) and os_path.exists(dst_dir_name) \
            and os_access(dst_dir_name, R_OK) and os_access(dst_dir_name, W_OK):
        if os_path.exists(dst) and rename_if_dst_exists:
            dst = auto_rename_file(dst)
        elif os_path.exists(dst) and not rename_if_dst_exists:
            log(msg='The file: "%s", already exist.!!' % dst, verbose=verbose, re_print=re_print, lvl=1)
            return False

        if ver.py.short >= 3.4:
            with suppress(Exception, shutil_Error):
                mv(src, dst)
                return True
            log(msg='Could not move "%s" to "%s".!!' % (src, dst), verbose=verbose, re_print=re_print, lvl=1)
            return False
        else:
            try:
                mv(src, dst)
            except (Exception, shutil_Error) as _:
                log(msg='Could not move "%s" to "%s".!!' % (src, dst), verbose=verbose, re_print=re_print, lvl=1)
                return False
            else:
                return True
    else:
        log(msg='Something is wrong with either "%s" or "%s"!' % (src, dst), verbose=verbose, re_print=re_print, lvl=1)
        return False


# ----------------------------------------------------------------------


def remove_files_except(keep=0 or '', files=None, verbose=False, re_print=True) -> bool:
    """ Removes all files, except the one with the given key.

        keep: Could be an integer represents the element key in 'files', or string as one of the 'files' elements.
        files: Should be a list, that holds the files which need to be removed. """

    if not files or (not keep and keep != 0) or type(files) != list or type(keep) not in (int, str) \
            or (type(keep) == int and
                (not os_path.exists(files[keep]) or keep not in range(len(files)))) \
            or (type(keep) == str and
                (not os_path.exists(keep) or keep not in files)):
        return False

    ret = True

    for k, f in enumerate(files):
        if keep in (k, f):
            p('    [+] [%s] %s' % (k + 1, f))
        else:
            if os_path.exists(f):
                if remove_file(f):
                    p('    [-] [%s] %s' % (k + 1, f))
                else:
                    log(msg='Could not remove "%s".!!' % f, verbose=verbose, re_print=re_print, lvl=1)
                    ret = False
            else:
                log(msg='Somehow the file "%s", does not exist at the time of removal.!!' % f, verbose=verbose,
                    re_print=re_print, lvl=1)
                ret = False

    return ret


def remove_file(file='', verbose=False, re_print=True) -> bool:
    dir_name = os_path.dirname(file)
    # TODO: do we really need the write permission to the folder that has the file we want to remove?
    if os_path.exists(file) and os_path.isfile(file) and os_access(file, R_OK) and os_access(file, W_OK) \
            and os_access(dir_name, R_OK) and os_access(dir_name, W_OK):
        # URL: https://stackoverflow.com/questions/10840533/most-pythonic-way-to-delete-a-file-which-may-not-exist
        # URL: https://docs.python.org/3/library/contextlib.html#contextlib.suppress
        if ver.py.short >= 3.4:
            # with suppress(FileNotFoundError):
            with suppress(FileNotFoundError, IsADirectoryError, OSError):
                os_remove(file)
                return True
            log(msg='Could not remove "%s".!!' % file, verbose=verbose, re_print=re_print, lvl=1)
            return False
        else:
            try:
                os_remove(file)
            # this would be "except OSError, e:" before Python 2.6
            # if e.errno != errno.ENOENT:   # errno.ENOENT = no such file or directory
            #    raise                      # re-raise exception if a different error occurred
            except (FileNotFoundError, IsADirectoryError, OSError) as _:
                log(msg='Could not remove "%s".!!' % file, verbose=verbose, re_print=re_print, lvl=1)
                return False
            else:
                return True
    else:
        log(msg='Something is wrong with the given file to remove "%s"!' % file,
            verbose=verbose, re_print=re_print, lvl=1)
        return False


# ------------------------------
#        MULTIPROCESSING
#               &
#           THREADING
# ------------------------------


def has_multiple_cores() -> bool:
    """ Return True if the system has multiple cores, otherwise False."""

    return cpu_count() > 1


# ------------------------------
#           HELPERS
# ------------------------------


def _exit(msg=None, status=1) -> None:
    """ Prints the given msg if there is any, then exit app with the given exit code. """

    if msg is not None:
        p(msg)
    sys_exit(status)


# ----------------------------------------------------------------------


if __name__ == '__main__':
    p('This file is part of DuGu package.')
    _exit('And is not meant to run directly.')
