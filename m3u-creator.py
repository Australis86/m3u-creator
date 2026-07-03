#!/usr/bin/env python3

"""This script creates an ordered M3U playlist from a source directory tree."""

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


def searchDirectoryTree(init_path, filtering_dict, sortmethod='ascii'):
    '''Search the directory tree for matching file types, sorting
    by the selected method. Returns a list of absolute file paths.

    filtering_dict = {
        'filetypes': list of file extensions to search for (required),
        'directory-include': list of keywords to match in paths (optional),
        'directory-exclude': list of keywords to exclude in paths (optional),
        'file-include': list of keywords to match in filenames (optional),
        'file-exclude': list of keywords to exclude in filenames (optional),
    }'''

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
        if sortmethod == 'ascii':
            subdirs.sort()
            files.sort()
        elif sortmethod == 'natural' and natsorted is not None:
            naturalsort = natsort_keygen(alg=ns.IGNORECASE)
            subdirs.sort(key=naturalsort)
            files.sort(key=naturalsort)

        # If no sorting is conducted, os.walk will fall back to its
        # default behaviour as per listdir

        # If directory inclusion is enabled, check that we're in a relevant subdirectory

        # Filter paths:
        #   1. if include list is present, check the path and disregard
        #      present directory if there are no matches
        #   2. if exclude list is present, check the path and disregard
        #      present directory if there are any matches
        inclusion_test = filtering_dict['directory-include'] and not any(w.lower() in path.lower() for w in filtering_dict['directory-include'])
        exclusion_test = filtering_dict['directory-exclude'] and any(w.lower() in path.lower() in path for w in filtering_dict['directory-exclude'])
        if inclusion_test or exclusion_test:
            continue

        # Filter files:
        #   1. filetypes - use the last extension to avoid issues where
        #      filenames contain a period
        #   2. if include list is present, check the filename and disregard
        #      files where there are no matches
        #   3. if exclude list is present, check the filename and disregard
        #      files where there are any matches
        filtered_files = files

        if filtering_dict['file-include']:
            filtered_files = [ f for f in filtered_files if any(w.lower() in f.lower() for w in filtering_dict['file-include']) ]
        if filtering_dict['file-exclude']:
            filtered_files = [ f for f in filtered_files if not any(w.lower() in f.lower() for w in filtering_dict['file-exclude']) ]

        filtered_files = [ os.path.join(path, f) for f in filtered_files if os.path.splitext(f)[-1] in filtering_dict['filetypes'] ]
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Create an ordered M3U playlist by scanning a directory tree for matching file types."
    )

    parser.add_argument("playlist",
        help="Filename for your playlist; e.g. music.m3u")
    parser.add_argument("-t","--top-directory",
        default=os.getcwd(),
        help="Top-level directory to search within for files to add to playlist (default: current working directory)")

    # File filtering
    parser.add_argument(
        "-f","--filetypes",
        nargs="*",
        default=[".mp3",".flac",".ogg",".wma",".wav",".webm",".aac",".m4a",".m4b"],
        help="File extensions to include as a space-separated list")
    parser.add_argument(
        "--file-exclude",
        nargs="*",
        default=None,
        help='Space-separated words or phrases to filter on; any filenames containing any of these entries will be excluded. Example list: "Track 01" "Track 02" "Promo" ')
    parser.add_argument(
        "--file-include",
        nargs="*",
        default=None,
        help='Space-separated words or phrases to filter on; any filenames NOT containing one of these entries will be excluded. Example list: "Track 01" "Track 02" "Promo" ')
    parser.add_argument(
        "--directory-exclude",
        nargs="*",
        default=None,
        help='Space-separated words or phrases to filter on; any directories containing any of these entries will be excluded. Example list: "Artist 1" "Artist 2" "Album" ')
    parser.add_argument(
        "--directory-include",
        nargs="*",
        default=None,
        help='Space-separated words or phrases to filter on; any directories NOT containing one of these entries will be excluded. Example list : "Artist 1" "Artist 2" "Album" ')

    # Playlist structure
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
    parser.add_argument(
        "-s","--sort-method",
        default="ascii",
        choices=["ascii","natural","unsorted"],
        help="Method used to sort the playlist (default: ascii)")

    args = parser.parse_args()

    filter_dict = {
        'filetypes':args.filetypes,
        'directory-include':args.directory_include,
        'directory-exclude':args.directory_exclude,
        'file-include':args.file_include,
        'file-exclude':args.file_exclude
    }

    (mediafiles, ec1) = searchDirectoryTree(args.top_directory, filter_dict, args.sort_method)
    # pylint: disable-next=C0103
    ec2 = buildPlaylist(mediafiles, args.playlist, args.top_directory, args.relative, args.extm3u)
    sys.exit(ec1 or ec2)
