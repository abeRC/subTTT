# subTTT: Subtitle Timestamp Tweaker Tool v0.9

## Overview
This program applies a time translation to the timestamps in SubRip subtitle 
files (.srt format).
The time translation (forward or backward shift) should be given as a float
and in seconds. Minus signs are interpreted as a backward shift (so the 
subtitles will be shown earlier than before).


Currently, there is only compatibility with subtitle files that have timestamps like this:

`00:01:43,108 --> 00:01:44,796`


## Installation and Usage
There is none. Just download the script and run it with
`python subttt.py [OPTIONS]... SRTFILE SHIFT`.

Accepted options: 
``` 
  -h, --help                 display this help and exit
  -v, --version              output version information and exit
      --replace              replace the original file
```


## Bugs
There ought to be.

## TODO
* add --fix0sec to fix 0 second subtitles
* verify if we need to work with bytes or if this gizmo is comprehensive enough
* compatibility with other formats
