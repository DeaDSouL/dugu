# dugu
The Duplicates Guru

### What is dugu?
`dugu` is a tool that helps to you find, remove and avoid the duplicates. It was inspired by the `fdupes`.

### Who wrote it? (Author)
Mubarak Alrashidi, who's known as DeaDSouL.


### Installation

It's not clear for now, how it's going to be installed. Since it's not being packaged yet.

Requires (minimum) Python 3.8.6

But you can download it, then manually install it by:

**Globally:** (don't forget the `su`/`sudo`)

    $ mv src /usr/local/src/dugu
    $ ln -s /usr/local/src/dugu/dugu.py /usr/local/bin/dugu

**Or Locally:**

    $ mv src ~/.local/share/dugu
    $ ln -s ~/.local/share/dugu/dugu.py ~/bin/dugu


### The argument 'scan'
This argument is meant for finding and/or getting rid of the duplicates.

### The argument 'precopy'
This argument is very handy and useful if you want to copy folders.
Its main purpose is avoiding the duplicates.


### Usage:
`dugu [-h] [-V] [-v] [-s] [-S] [-f] [-t {md5,sha1,sha256,sha512}] [-p | -l | -L | -i | -r | -R] scan DIR | precopy DIR1 DIR2`


### How to
Let's say we want to check the folder called: 'Pictures':


If you only want to scan 'Pictures', try:

    dugu scan Pictures

If you want to see the list of duplicates, try:

    dugu -p scan Pictures

If you want to visually see the duplicates (using: soft-links), try:

    dugu -l scan Pictures

If you want to visually see the duplicates (using: hard-links), try:

    dugu -L scan Pictures

If you want to isolate all the duplicates, try:

    dugu -i scan Pictures

If you want to remove the duplicates, try:

    dugu -r scan Pictures

If you want to auto-remove the duplicates, try:

    dugu -R scan Pictures

If you want to ignore the cache, and force dugu to re-scan 'Pictures', try:

    dugu -f scan Pictures

If you want to use 'sha1' as the scan's algorithm, try:

    dugu -t sha1 scan Pictures

If you want to follow all links that point to files, try:

    dugu -s scan Pictures

If you want to follow all links that point to directories, try:

    dugu -S scan Pictures

If you want to exclude the files in the folder 'old_pic' that folder 'Pictures' already have, try:

    dugu precopy old_pic Pictures
PS: Please note, that the previous command will only exclude the files from 'old_pic' that are being existed in both directories. It **will not** touch the duplicates that might be in 'old_pic'; Unless you use one of `[-p | -l | -i | -r | -R]` with the argument `precopy`

For example, if you want to auto-remove the duplicates found in the produced files, try:

    dugu -r precopy old_pic Pictures

To get the help menu, try:

    dugu -h

### License
Although, this program is a free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see [gnu.org/licenses](http://www.gnu.org/licenses/).

Copyright (C) [DeaDSouL](https://github.com/DeaDSouL)
