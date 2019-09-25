#!/usr/bin/python
#/usr/bin/env python2
# -*- coding: UTF-8 -*-
# By: DeaDSouL (Mubarak Alrashidi)
#---------------------------------
# 
# @TODO CODE:
# 01.    Change the way 'precopy' works.
#            A.  Instead of copying the whole 'DIR1' then deleting the duplicates
#                copy only the 'DIR1' structure, then copying the unique files.
#            B.  Instead of placing '_UniqueFiles_' under 'DIR1', put it in tmp path.
# 

import os
import hashlib
import cPickle as pickle
import argparse
import time
from tempfile import mkdtemp, gettempdir
from stat import S_ISSOCK
from shutil import rmtree, copytree, move
from distutils.dir_util import copy_tree
from getpass import getuser
from sys import exit

class dugu:

    # ------------------------------------------------------------------

    # generated vars
    scan_result    = {'total_files':0, 'files':{}}
    dups_result    = {'total_files':0, 'hash_type':'md5', 'dups_sets':0, 'dups_count':0, 'dups_size':0, 'dups':{}}
    cwd            = ''
    cache_dir      = ''
    report_dir     = ''
    dugu_path      = ''
    # tmp vars
    counter        = 0
    tmp_dup_list   = {}
    tmp_flash      = {}
    # app vars
    wait_symbols   = ('\\', '|', '/', '--', '|')
    dtformat       = '%Y-%m-%d %H:%M:%S'
    args           = ''

    # ------------------------------------------------------------------

    def __init__(self):
        self.__init_temp()
        self.__init_parser()
        self.__initCache()
        print ''

    # ------------------------------------------------------------------

    def __init_temp(self):
        self.dugu_path = os.path.abspath(gettempdir())
        dugu_path = self.__buildPath( ('dugu_%s' % getuser() ) )
        if not os.path.exists(dugu_path):
            dtmp = mkdtemp()
            move(dtmp, dugu_path)
        self.dugu_path = dugu_path[:]

    # ------------------------------------------------------------------

    def __init_parser(self):
        parser = argparse.ArgumentParser(prog='DUGU', description='Duplicated files manager tool.')
        parser.add_argument('-v', '--verbose', action='store_true',
                    help='Increase output verbosity. (not fully implemented yet)')
        parser.add_argument('-s', '--symlinks', action='store_true', default=False,
                    help='Include symbolic links in the scanning. (not recommended) (not implemented yet)')
        parser.add_argument('-f', '--force', action='store_true', default=False,
                    help='Ignoring the generated cache.')
        parser.add_argument('-t', '--hashtype', type=str, choices=['md5', 'sha1', 'sha256', 'sha512'],
                    default='md5', help='The algorithm to be used in scanning files. (default: md5)')

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-p', '--print_duplicates', action='store_true', default=False, help='will print all the duplicated files categorized by their sets. Please note that, this argument is meant to only work with argument "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected optional arguments with "scan" to the produced directory "_UniqueFiles_".')
        group.add_argument('-l', '--links', action='store_true', default=False, help='will generate a folder that has symlinks to all the duplicated files categorized by their sets. Please note that, this argument is meant to only work with argument "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected optional arguments with "scan" to the produced directory "_UniqueFiles_".')
        group.add_argument('-i', '--isolate', action='store_true', default=False, help='will move the duplicated files to a folder called "isolate" under the temporary folder in your operating-system. Please note that, this argument is meant to only work with argument "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected optional arguments with "scan" to the produced directory "_UniqueFiles_".')
        group.add_argument('-r', '--remove', action='store_true', default=False, help='will prompt user for files to preserve and remove all others; important: under particular circumstances, data may be lost when using this option together with -s or --symlinks. Please note that, this argument is meant to only work with argument "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected optional arguments with "scan" to the produced directory "_UniqueFiles_".')
        group.add_argument('-R', '--autoremove', action='store_true', default=False, help='will preserve the first file in each set of duplicates and remove the rest without prompting the user. Please note that, this argument is meant to only work with argument "scan"; So if it is being called with argument "precopy", it will first execute the "precopy" to "dir1", then will execute the same selected optional arguments with "scan" to the produced directory "_UniqueFiles_".')

        subparsers = parser.add_subparsers(help='Main Commands', dest='cmd')
        parser_scan = subparsers.add_parser('scan', help='(ex: scan "path/to/dir") To preform a normal scan for the duplicated files, followed by the path of the directory.')
        parser_scan.add_argument('DIR', type=str, nargs='?', action='store', default=os.getcwd(), help='The path of the directory to scan.')
        parser_precopy = subparsers.add_parser('precopy', help='(ex: precopy "path/to/dir1" "path/to/dir2"): To execlude all the files in "dir1" that already in "dir2", and put the unique files in a folder called "_UniqueFiles_" inside "dir1" with the same structure of "dir1".')
        parser_precopy.add_argument('DIRS', type=str, nargs=2, action='store', help='Expects 2 dirs: DIR_FROM and DIR_TO.')

        self.args = parser.parse_args()

    # ------------------------------------------------------------------

    def main(self): # print sys.argv
        if self.args.verbose:
            self.__msg('Verbosity mode is ON')

        # Main cmd
        if self.args.cmd == 'scan':
            self.__isExistedDir( self.args.DIR )
            self.__setcwd(self.args.DIR)
            self.findDups()
        elif self.args.cmd == 'precopy':
            self.__isExistedDir( self.args.DIRS )
            if self.preCopy(self.args.DIRS[0], self.args.DIRS[1]):
                if self.args.print_duplicates or self.args.links or self.args.isolate or self.args.remove or self.args.autoremove:
                    print ''
                    self.args.cmd = 'scan'
                    org_cwd = self.cwd[:]
                    self.__setcwd(self.tmp_flash['uniqueDir'])
                    self.findDups()
                    self.__setcwd(org_cwd)
                    self.args.cmd = 'precopy'
        else:
            pass

        self.__exit(status=0)

    # ------------------------------------------------------------------

    def findDups(self):
        self.scan_result['total_files'] = self.__countFiles()
        self.dups_result['total_files'] = self.scan_result['total_files']

        if self.args.force: self.__preScanDir()
        else: self.__loadCache()

        if self.dups_result['dups_count'] == 0:
            print '---------------------------'
            print 'No duplicates found.'
        else:
            if self.args.print_duplicates:
                self.__printDuplicates()
            elif self.args.isolate:
                self.__autoIsolateDuplicates()
            elif self.args.remove:
                self.__removeDuplicatesPrompt()
            elif self.args.autoremove:
                self.__autoRemoveDuplicates()

            #print 'Found: (%s) duplicated files in (%s) sets. occupying %s, with the same (%s) signature:' % (self.dups_result['dups_count'], self.dups_result['dups_sets'], self.sizeof_fmt(self.dups_result['dups_size']), self.args.hashtype)
            print ''
            print '   Total Files : %s' % self.scan_result['total_files']
            print '    Duplicates : %s' % self.dups_result['dups_count']
            print '          Sets : %s' % self.dups_result['dups_sets']
            print '     Occupying : %s' % self.sizeof_fmt(self.dups_result['dups_size'])
            print 'Hash Signature : %s' % self.args.hashtype

            if self.args.links:
                print ''
                print 'Please check: %s' % self.report_dir
                print ''

    # ------------------------------------------------------------------

    def preCopy(self, src='', dst=''):
        if not os.path.isdir(src):
            print '%s : is not directory' % src
            return False
        if not os.path.isdir(dst):
            print '%s : is not directory' % dst
            return False

        self.tmp_flash['uniqueDir'] = os.path.abspath(os.path.join(src, '_UniqueFiles_'))

        if os.path.isdir(self.tmp_flash['uniqueDir']):
            answer = None
            while answer not in ('y','n'):
                if answer != None:
                    print 'Invalid input!'
                print '"%s" exists! Do you want to remove it first? (y/n)\r' % self.tmp_flash['uniqueDir']
                answer = raw_input(' ')

            if answer == 'n':
                print 'Aborting,... \r'
                return False
            else:
                rmtree(self.tmp_flash['uniqueDir'])

        # Copy directory with its all contents
        print 'Copying Files....                                         \r',
        # using `preserve_symlinks=1` in `copy_tree()` will fix issue #1
        self.tmp_flash['copiedFiles'] = copy_tree(src, self.tmp_flash['uniqueDir'], preserve_symlinks=1)
        print 'Copying Files..........Done                               \r'

        org_cwd = self.cwd[:]
        self.__setcwd(dst)

        self.scan_result['total_files'] = self.__countFiles('dst')

        if self.args.force: self.__prePreCopy()
        else: self.__loadCache()

        # Source Dir
        self.__resetApp()
        self.__setcwd(self.tmp_flash['uniqueDir'])
        self.scan_result['total_files'] = self.__countFiles('src')
        self.__scanDir(self.cwd)
        print 'Scanning SRC Files.....Done                               \r'
        self.tmp_flash['src_info'] = self.scan_result.copy()
        self.__resetApp()

        self.__setcwd(org_cwd)

        self.tmp_flash['dst_hashes'] = []
        # arr[0]=size, arr[1]=mtime, arr[2]=hash
        for file,arr in self.tmp_flash['dst_info']['files'].iteritems():
            self.tmp_flash['dst_hashes'].append(arr[2])
        print 'Generating DST Files...Done                               \r'

        i = 0
        # arr[0]=size, arr[1]=mtime, arr[2]=hash
        for file,arr in self.tmp_flash['src_info']['files'].iteritems():
            if arr[2] in self.tmp_flash['dst_hashes']:
                i += 1
                os.remove(file)

        print 'Removing Duplicates....Done                               \r'
        print '----------------------------'
        print 'Removed (%s) files from source directory.' % i
        print 'Because they exist in the destination.'
        print ' '
        print 'Please check: "%s"' % self.tmp_flash['uniqueDir']

        return True

    # ------------------------------------------------------------------

    def __prePreCopy(self):
        self.__removeCache()
        self.__scanDir(self.cwd)
        print 'Scanning DST Files.....Done                               \r'
        self.__saveCache()
        self.tmp_flash['dst_info'] = self.scan_result.copy()
        self.__resetApp()

    # ------------------------------------------------------------------

    def __preScanDir(self):
        self.__removeCache()
        self.__removeReport()
        self.__resetApp()

        self.__scanDir(self.cwd)
        print 'Scanning Files.........Done                               \r'

        count,size = 0,0
        for sig,files in self.dups_result['dups'].iteritems():
            count += len(files)-1
            size += os.path.getsize(files[0])*(len(files)-1)

        self.dups_result['hash_type']   = self.args.hashtype
        self.dups_result['total_files'] = self.scan_result['total_files']
        self.dups_result['dups_sets']   = len(self.dups_result['dups'])
        self.dups_result['dups_count']  = count
        self.dups_result['dups_size']   = size

        self.__saveCache()
        self.__generateReport()

    # ------------------------------------------------------------------

    def __scanDir(self, cPath=None):
        if cPath == None:
            cPath = self.cwd
        for f in os.listdir(cPath):
            ff = os.path.abspath(os.path.join(cPath,f))

            if os.path.islink(ff):
                # TODO: may be we should use 'and' instead of 'or' ??
                if self.cwd not in os.path.realpath(ff) or not self.args.symlinks:
                    self.__msg('Ignoring Link: %s' % ff)
                    continue

            if not os.path.exists(ff):
                self.__msg('Ignoring Inexistent: %s' % ff)
            elif not os.access(ff, os.R_OK):
                self.__msg('Ignoring Unreadable: %s' % ff)
            elif S_ISSOCK(os.stat(ff).st_mode):
                self.__msg('Ignoring Socket: %s' % ff)
            elif os.path.isfile(ff):
                self.counter += 1
                print 'Scanning Files: (%d/%d) - %d%% \r' % (self.counter, self.scan_result['total_files'], (self.counter*100/self.scan_result['total_files'])),
                dt_modified = time.strftime(self.dtformat, time.localtime(os.path.getmtime(ff)))
                size        = os.path.getsize(ff)
                hashSig     = self.__getFileSum(ff, self.args.hashtype)
                self.scan_result['files'][ff] = [size, dt_modified, hashSig]

                if self.args.cmd == 'scan':
                    if hashSig in self.tmp_dup_list:
                        if hashSig not in self.dups_result['dups']:
                            self.dups_result['dups'][hashSig] = []
                        if self.tmp_dup_list[hashSig] != ff and self.tmp_dup_list[hashSig] not in self.dups_result['dups'][hashSig]:
                            self.dups_result['dups'][hashSig].append(self.tmp_dup_list[hashSig])
                        if ff not in self.dups_result['dups'][hashSig]:
                            self.dups_result['dups'][hashSig].append(ff)
                    else:
                        self.tmp_dup_list[hashSig] = ff

            elif os.path.isdir(ff):
                self.__scanDir(ff)

            else: self.__msg('Unknown: %s' % ff)

    # ------------------------------------------------------------------

    def __initCache(self):
        self.cache_dir = self.__buildPath( ('cache') )
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    # ------------------------------------------------------------------

    def __saveCache(self):
        if self.args.cmd == 'precopy':
            cPre2Path = self.__getCachePathOf('precopy_dst', self.args.DIRS[1])
            pickle.dump( self.scan_result, open( cPre2Path, 'wb' ) )
        else:
            cDupsPath = self.__getCachePathOf('dups')
            cScanPath = self.__getCachePathOf('scan')
            pickle.dump( self.dups_result, open( cDupsPath, 'wb' ) )
            pickle.dump( self.scan_result, open( cScanPath, 'wb' ) )

    # ------------------------------------------------------------------

    def __loadCache(self):
        # TODO: re-write function, to avoid the duplicated lines of code
        if self.args.cmd == 'precopy':
            cPre2Path = self.__getCachePathOf('precopy_dst', self.args.DIRS[1])
            if os.path.isfile(cPre2Path):
                cPre2 = pickle.load( open( cPre2Path, 'rb' ) )
            if 'cPre2' in locals():
                if cPre2['total_files'] == self.scan_result['total_files']:
                    self.scan_result = cPre2
                    self.tmp_flash['dst_info'] = cPre2.copy()
                    if self.__validatedCache():
                        print 'Validating Cache.......Done                              \r'
                        print 'Loading DST Cache......Done \r'
                    else:
                        print 'Changes Detected.......Done \r'
                        self.__prePreCopy()
                else:
                    print 'Changes Detected.......Done \r'
                    self.__prePreCopy()
            else:
                self.__prePreCopy()
        else:
            cDupsPath = self.__getCachePathOf('dups')
            cScanPath = self.__getCachePathOf('scan')

            if os.path.isfile(cDupsPath):
                cDups = pickle.load( open( cDupsPath, 'rb' ) )
            if os.path.isfile(cScanPath):
                cScan = pickle.load( open( cScanPath, 'rb' ) )

            if 'cDups' in locals() and 'cScan' in locals():
                if cScan['total_files'] == self.scan_result['total_files']:
                    self.dups_result = cDups
                    self.scan_result = cScan
                    dups_sum = 0
                    for sig,files in self.dups_result['dups'].iteritems():
                        dups_sum += len(files)-1
                    if not self.__validatedCache() or self.dups_result['dups_count'] != dups_sum or self.dups_result['dups_sets'] != len(self.dups_result['dups']):
                        print 'Changes Detected.......Done \r'
                        self.__preScanDir()
                    else:
                        print 'Validating Cache.......Done                              \r'
                        print 'Loading Cache..........Done \r'
                        self.__generateReport()
                else:
                    print 'Changes Detected.......Done \r'
                    self.__preScanDir()
            else:
                self.__preScanDir()

    # ------------------------------------------------------------------

    def __validatedCache(self):
        if self.scan_result['total_files'] != len(self.scan_result['files']):
            return False
        i = 0
        # arr[0]=size, arr[1]=mtime, arr[2]=hash
        for file,arr in self.scan_result['files'].iteritems():
            i += 1
            print 'Validating Cache: (%d/%d) - %d%% \r' % (i, self.scan_result['total_files'], (i*100/self.scan_result['total_files'])),
            if not os.path.exists(file) or not os.path.isfile(file):
                print 'Missing Files Detected.Done                              \r'
                return False
            if arr[0] != os.path.getsize(file):
                print 'Diff Sizes Detected....Done                              \r'
                return False
            if arr[1] != time.strftime(self.dtformat, time.localtime(os.path.getmtime(file))):
                print 'Diff mTime Detected....Done                              \r'
                return False
        return True

    # ------------------------------------------------------------------

    def __removeCache(self):
        if self.args.cmd == 'precopy':
            cPre2Path = self.__getCachePathOf('precopy_dst', self.args.DIRS[1])
            cFiles = [cPre2Path]
        else:
            cDupsPath = self.__getCachePathOf('dups')
            cScanPath = self.__getCachePathOf('scan')
            cFiles = [cDupsPath, cScanPath]

        cacheExists = False
        for cFile in cFiles:
            if os.path.exists(cFile) and os.path.isfile(cFile):
                os.remove(cFile)
                cacheExists = True
        
        if cacheExists: print 'Removing Old Cache.....Done'
        self.__resetApp()

    # ------------------------------------------------------------------

    def __getCachePathOf(self, of='dups', cwd=None):
        if cwd == None or not os.path.isdir(cwd):
            cwd = self.cwd

        # (cwd-md5-sig)_(md5|sha1|sha256|sha512)_(scan|dups).pkl
        sig = hashlib.md5(str(cwd).encode('utf-8')).hexdigest()

        if of == 'precopy_dst':
            cacheFile = '%s_%s_pdst.pkl' % (sig, self.args.hashtype)
        elif of == 'scan':
            cacheFile = '%s_%s_scan.pkl' % (sig, self.args.hashtype)
        else:
            cacheFile = '%s_%s_dups.pkl' % (sig, self.args.hashtype)

        return os.path.join(self.cache_dir, cacheFile)

    # ------------------------------------------------------------------

    def __printDuplicates(self):
        print ''
        i1,i2 = 0,0
        for sig,files in self.dups_result['dups'].iteritems():
            i1 += 1
            print '%s) Signature: %s :' % (i1, sig)
            i2 = 0
            for file in files:
                i2 += 1
                print '        %s) %s' % (i2, file)
            print ''

    # ------------------------------------------------------------------

    def __autoIsolateDuplicates(self):
        tmp_sig = hashlib.md5(str(os.path.abspath(self.cwd)).encode('utf-8')).hexdigest()
        tmp_dirbase = self.__buildPath( ('result', '%s_%s' % (tmp_sig, self.args.hashtype)) )
        tmp_diriso = os.path.join(tmp_dirbase, 'isolated')

        i = 0
        tmp_dir = tmp_diriso[:]
        
        while os.path.isdir( tmp_dir ):
            i += 1
            tmp_dir = '%s_%s' % (tmp_diriso, i)

        self.tmp_flash['isolateDir'] = tmp_dir[:]

        self.__copyDirStructure(self.cwd, self.tmp_flash['isolateDir'])
        print 'Copying Dir Structure..Done \r'

        i = 0
        for sig,files in self.dups_result['dups'].iteritems():
            i += 1
            if i > 1:
                print '------------------------------------------------------------'
            print '[%s/%s] Signature: %s :' % (i, self.dups_result['dups_sets'], sig)
            if not os.path.exists(files[0]) or not os.path.isfile(files[0]) or os.path.islink(files[0]):
                print 'Ignoring this set.'
                continue
            self.__isolateAllExcept(0, files)
            if i == self.dups_result['dups_sets']:
                print '------------------------------------------------------------'

        print 'Please check: %s' % self.tmp_flash['isolateDir']

        print 'Know that, the above location will be gone if anything happens to'
        print 'the operating system such as restart, poweroff, crash... and so on'

    # ------------------------------------------------------------------

    def __isolateAllExcept(self, key=0, files=None):
        if files == None or key not in range(len(files)) or type(files) != list or not os.path.exists(files[key]):
            return False

        for k,f in enumerate(files):
            subpath = os.path.relpath(f, self.cwd)
            newf = os.path.join(self.tmp_flash['isolateDir'], subpath)
            if key == k:
                print '    [+] [%s] %s' % (k+1, f)
            else:
                print '    [-] [%s] %s' % (k+1, f)
                move(f,newf)

    # ------------------------------------------------------------------

    def __removeDuplicatesPrompt(self):
        i = 0
        for sig,files in self.dups_result['dups'].iteritems():
            i += 1
            if i > 1:
                print '------------------------------------------------------------'
            print '[%s/%s] Signature: %s :' % (i, self.dups_result['dups_sets'], sig)
            for key,file in enumerate(files):
                print '        [%s] %s' % (key+1, file)

            c = None
            options = '1-%s, all or exit: ' % (key+1)
            while c not in range(1,key+2):
                if c == 'all':
                    break
                elif c == 'exit':
                    print 'Exiting,...'
                    return False
                elif c != None:
                    print 'Invalid choice!'

                print 'Which file would you like to preserve?'
                c = raw_input(options)
                if c not in ('all', 'quit'):
                    try:
                        c = int(c)
                    except ValueError, e:
                        pass

            print ''

            if c == 'all':
                print 'Preserving all files in this set'
                for key,file in enumerate(files):
                    print '    [+] [%s] %s' % (key+1, file)
            else:
                selectedFile = files[c-1]
                selectedKey = c-1

                if not os.path.exists(selectedFile):
                    print 'The selected file to preserve, is somehow not available!'
                    print 'Ignoring this set.'
                    continue

                if os.path.islink(selectedFile):
                    answer = None
                    while answer not in ('YES','NO'):
                        if answer != None:
                            print ''
                            print 'Invalid answer!'
                            print ''
                        print 'The selected file to preserve, is a link.'
                        print 'This might cause loosing the actual file.'
                        print 'Are you sure you want to proceed ?'
                        answer = raw_input('YES/NO')
                    if answer == 'NO':
                        print 'Ignoring this set.'
                        continue

                self.__removeAllExcept(selectedKey, files)

            if i == self.dups_result['dups_sets']:
                print '------------------------------------------------------------'

    # ------------------------------------------------------------------

    def __autoRemoveDuplicates(self):
        i = 0
        for sig,files in self.dups_result['dups'].iteritems():
            i += 1
            if i > 1:
                print '------------------------------------------------------------'
            print '[%s/%s] Signature: %s :' % (i, self.dups_result['dups_sets'], sig)
            if not os.path.exists(files[0]) or not os.path.isfile(files[0]) or os.path.islink(files[0]):
                print 'Ignoring this set.'
                continue
            self.__removeAllExcept(0, files)
            if i == self.dups_result['dups_sets']:
                print '------------------------------------------------------------'

    # ------------------------------------------------------------------

    def __removeAllExcept(self, key=0, files=None):
        if files == None or key not in range(len(files)) or type(files) != list or not os.path.exists(files[key]):
            return False

        for k,f in enumerate(files):
            if key == k:
                print '    [+] [%s] %s' % (k+1, f)
            else:
                print '    [-] [%s] %s' % (k+1, f)
                os.remove(f)

    # ------------------------------------------------------------------

    def __generateReport(self):
        if self.dups_result['dups_count'] == 0 or not self.args.links:
            return False

        # (cwd-md5-sig)_(md5|sha1|sha256|sha512)/
        repDirSig = hashlib.md5(str(self.cwd).encode('utf-8')).hexdigest()

        self.report_dir = self.__buildPath( ('result', '%s_%s' % (repDirSig, self.args.hashtype), 'links') )

        if not os.path.exists(self.report_dir):
            # self.__msg('Creating new report directory: %s' % self.report_dir)
            os.makedirs(self.report_dir)
            print 'Creating New Report....Done'

            i = 0
            for sig,files in self.dups_result['dups'].iteritems():
                subRepDir = os.path.join(self.report_dir, sig)
                # self.__msg('Creating new set directory: %s' % subRepDir)
                os.makedirs(subRepDir)
                for file in files:
                    if i >= len(self.wait_symbols): i = 0
                    print 'Generating Report.... %s \r' % self.wait_symbols[i],
                    i += 1

                    symDest         = os.path.join(subRepDir, os.path.basename(file))

                    symSrcFName, symSrcFExt = os.path.splitext(file)
                    symSrcFName     = os.path.basename(symSrcFName)

                    i = 0
                    while os.path.isfile(symDest):
                        i += 1
                        symDest = os.path.join(subRepDir, '%s_%d%s' % (symSrcFName, i, symSrcFExt))

                    os.symlink(file, symDest)
            print 'Creating SymLinks......Done'
            print 'Generating Report......Done'
        else:
            print 'Loading Report.........Done'

    # ------------------------------------------------------------------

    def __removeReport(self):
        repDirSig = hashlib.md5(str(self.cwd).encode('utf-8')).hexdigest()
        self.report_dir = self.__buildPath( ('result', '%s_%s' % (repDirSig, self.args.hashtype), 'links') )
        if os.path.exists(self.report_dir):
            print 'Removing Old Report....Done'
            rmtree(self.report_dir)

    # ------------------------------------------------------------------

    # Getting md5, sha1, sha256, sha512 hash of the given file
    def __getFileSum(self, fname, hashType='md5'):
        if hashType == 'sha1': hash = hashlib.sha1()
        elif hashType == 'sha256': hash = hashlib.sha256()
        elif hashType == 'sha512': hash = hashlib.sha512()
        else: hash = hashlib.md5()

        with open(fname, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash.update(chunk)

        return hash.hexdigest()
        #return hash.digest()

    # ------------------------------------------------------------------

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    # ------------------------------------------------------------------

    def __setcwd(self, cwd=None):
        self.cwd = cwd[:]
        self.cwd = os.path.abspath(self.cwd)

    # ------------------------------------------------------------------

    def __isExistedDir(self, dirs=None):
        invalidDir = False
        
        if type(dirs) == tuple or type(dirs) == list:
            for d in dirs:
                self.__isExistedDir(d)
        elif dirs != None:
            if not os.path.exists(dirs) or not os.path.isdir(dirs):
                invalidDir = True
        else:
            invalidDir = True

        if invalidDir:
            print 'Invalid DIR: %s' % dirs
            self.__exit('Exiting,..')

    # ------------------------------------------------------------------

    def __exit(self, msg=None, status=1):
        if msg != None: print msg
        exit(status)
    # ------------------------------------------------------------------

    def __resetApp(self):
        self.counter = 0
        self.tmp_dup_list = {}
        self.scan_result['files'] = {}
        self.dups_result['dups'] = {}

    # ------------------------------------------------------------------

    # Count all the files in directory (recursively)
    def __countFiles(self, which=None):
        # this will count links AND sockets
        #self.total_files = sum((len(f) for _, _, f in os.walk(self.cwd)))

        total_files = 0
        i = 0
        for path, _, filenames in os.walk(self.cwd):
            for filename in filenames:
                if i >= len(self.wait_symbols): i = 0
                print 'Counting Files.... %s \r' % self.wait_symbols[i],
                i += 1
                filename_path = os.path.join(path, filename)
                if os.path.islink(filename_path):
                    # TODO: may be we should use 'and' instead of 'or' ??
                    if self.cwd not in os.path.realpath(filename_path) or not self.args.symlinks:
                        continue
                if os.path.exists(filename_path) and os.access(filename_path, os.R_OK) and not S_ISSOCK(os.stat(filename_path).st_mode):
                    total_files += 1

        if which == 'dst': print 'Counting DST Files.....Done \r'
        elif which == 'src': print 'Counting SRC Files.....Done \r'
        else: print 'Counting Files.........Done \r'

        return total_files

    # ------------------------------------------------------------------

    def __buildPath(self, dirs=None, isTemp=True):
        ret = self.dugu_path if isTemp else ''

        if type(dirs) == tuple or type(dirs) == list:
            for d in dirs:
                ret = os.path.join(ret, d)
        elif dirs != None:
            ret = os.path.join(ret, dirs)

        return ret

    # ------------------------------------------------------------------

    def __copyDirStructureCallableToIgnoreFiles(self, folder, names):
        return set(n for n in names if not os.path.isdir(os.path.join(folder, n)))

    # ------------------------------------------------------------------

    def __copyDirStructure(self, src, dst):
        if os.path.isdir(src) and not os.path.exists(dst):
            copytree(src, dst, ignore=self.__copyDirStructureCallableToIgnoreFiles)

    # ------------------------------------------------------------------

    def __copyDirStructureWithSourceBase(self, src, dst):
        src_base = os.path.basename(src)
        dst_w_base = os.path.join(dst,src_base)
        if os.path.isdir(src) and not os.path.exists(dst_w_base):
            copytree(src, dst_w_base, ignore=self.__copyDirStructureCallableToIgnoreFiles)

    # ------------------------------------------------------------------

    # @TODO: Debug, Warning, Error, messages
    def __msg(self, str=''):
        if self.args.verbose: print(str)

# ------------------------------------------------------------------


if __name__ == '__main__':
    try:
        dugu().main()
    except KeyboardInterrupt, e:
        pass
