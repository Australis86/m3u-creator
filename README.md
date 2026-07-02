# m3u-creator
Create an ordered M3U playlist from a source directory tree.

## Background

I wrote this script as a result of other available solutions relying on
Python's os.walk() and hence not producing an ordered output. The purpose
was to have a way to create a playlist of albums or audiobooks that 
preserved the file order for each subdirectory and would optionally 
accept a list of input folders to use as well.

Related scripts (better suited to randomized music playlists):

- https://github.com/bellerofonte/m3u-creator
- https://pypi.org/project/m3u-maker/

No LLMs were used in the creation of this script.


## Dependencies

Python packages:

- [natsort](https://pypi.org/project/natsort/) -- optional; required to enable natural sorting
- [music-tag](https://pypi.org/project/music-tag/) -- optional; required to enable extended M3U parameters


## Usage

The script requires you to specify the output playlist name.

Optional arguments:

| parameter | example | description |
| --- | --- | --- |
| -t, --top-directory | /path/to/your/music | Set the top level directory for the search. Default is the current working directory. |
| -f, --filetypes | .mp3 .flac .ogg | Specify what file types to search for; currently this matches only on file extension and does not inspect the file headers. Default is some common audio formats. |
| -s, --sort-method | ascii | Specify which sort method to use on the playlist. The default behaviour is 'ascii', which tries to match the default Unix ls and Windows Explorer (pre Windows 10) sort order. If the `natsort` package is installed, you can also specify 'natural' as the sort order. 'unsorted' uses the default behaviour of `os.walk`. |
| -r, --relative | | Boolean flag to force the use of relative paths in the playlist (paths will be relative to the starting top level directory). Default behaviour is to use absolute paths. |
| -e, --extm3u | | Boolean flag to request the inclusion of EXTM3U and EXTINF tags in the playlist. Requires the `music-tag` package. |


# Copyright and Licence

Unless otherwise stated, these scripts are Copyright © Joshua White and 
licensed under the GNU GPL v3.0.
