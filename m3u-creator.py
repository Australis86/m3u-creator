#!/usr/bin/env python3
#
#  m3u-creator.py
#  
#  Copyright 2026 Joshua White
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  See README.MD or https://github.com/Australis86/m3u-creator 
#  for documentation


import sys
import os
import argparse

try:
    from natsort import natsorted, natsort_keygen, ns
except ImportError:
    natsorted = None
try:
    import music_tag
except ImportError:
    music_tag = None


def searchDirectoryTree(init_path, filetypes, sortmethod='ascii'):
    '''Search the directory tree for matching file types, sorting 
    by the selected method. Returns a list of absolute file paths.'''

    ec = 0 # Exit code

    if sortmethod == 'natural' and natsorted is None:
        print(os.linesep,"ERROR: natsort package missing -- natural sorting not available, falling back to ascii",os.linesep)
        sortmethod = 'ascii'
        ec = 2
        
    print(f"Searching {init_path}...")
    results = []

    for path, subdirs, files in os.walk(init_path):
        # os.walk yields at each step, so by sorting here we can 
        # influence the order in which the directory tree is recursed
        
        # Sort the subdirectories and folders
        if sortmethod == 'alphabetical':
            subdirs.sort()
            files.sort()
        elif sortmethod == 'natural' and natsorted is not None:
            naturalsort = natsort_keygen(alg=ns.IGNORECASE)
            subdirs.sort(key=naturalsort)
            files.sort(key=naturalsort)

        # If no sorting is conducted, os.walk will fall back to its 
        # default behaviour as per listdir
        
        # Filter files based on filetypes - use the last extension to
        # avoid issues where filenames contain a period
        filtered_files = [ os.path.join(path, f) for f in files if os.path.splitext(f)[-1] in filetypes ]
        found_files = len(filtered_files)
        if found_files > 0:
            print(f"{found_files} file(s) in {path}")
            
        results.extend(filtered_files)
        
    return (results, ec)


def buildPlaylist(filelist, playlist, init_path, relpaths=False, extended_m3u=False):
    '''Create the M3U playlist. Include EXTM3U and EXTINF if requested.
    EXTINF tags are of format: #EXTINF:LENGTH, ARTIST - TRACK'''
    
    ec = 0 # Exit code
    
    if extended_m3u and music_tag is None:
        print(os.linesep,"ERROR: music-tag package missing -- extended M3U is not available, falling back to basic M3U",os.linesep)
        extended_m3u = False
        ec = 2
    
    with open(playlist, 'w', encoding='utf-8') as f:
        if extended_m3u:
            f.write("#EXTM3U\n")
            for filepath in filelist:
                # Read the file length, artist and title from metadata
                # Fall back to the album artist if artist is blank for some reason
                metadata = music_tag.load_file(filepath)
                track_length = int(round(metadata['#length'].value))
                artist = metadata['artist'].value or metadata['albumartist'].value
                track_title = metadata['tracktitle'].value

                # Write the playlist entry
                f.write(f'#EXTINF:{track_length},{artist} - {track_title}\n')
                if relpaths:
                    f.write(os.path.relpath(filepath, start=init_path) + '\n')
                else:
                    f.write(filepath + '\n')
        else:
            for filepath in filelist:
                if relpaths:
                    f.write(os.path.relpath(filepath, start=init_path) + '\n')
                else:
                    f.write(filepath + '\n')

        f.close()

    return ec


def main(args):
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Create an ordered M3U playlist by scanning a directory tree for matching file types."
    )
    
    parser.add_argument("playlist",
        help="Filename for your playlist; e.g. music.m3u")
    parser.add_argument("-t","--top-directory",
        default=os.getcwd(),
        help="Top-level directory to search within for files to add to playlist (default: current working directory)")
    parser.add_argument(
        "-f","--filetypes",
        nargs="*",
        default=[".mp3",".flac",".m4b",".wav",".aac"],
        help="File extensions to include as a space-separated list")
    parser.add_argument(
        "-s","--sort-method",
        default="ascii",
        choices=["ascii","natural","unsorted"],
        help="Method used to sort the playlist (default: ascii)")
    parser.add_argument(
        "-e","--extm3u",
        action="store_true",
        default=False,
        help="Write the EXTM3U and EXTINF tags")
    parser.add_argument(
        "-r","--relative",
        action="store_true",
        default=False,
        help="Use relative paths in the playlist rather than absolute")

    args = parser.parse_args()

    (mediafiles, ec1) = searchDirectoryTree(args.top_directory, args.filetypes, args.sort_method)
    ec2 = buildPlaylist(mediafiles, args.playlist, args.top_directory, args.relative, args.extm3u)
    exit(ec1 or ec2)
