# subTTT: Subtitle Timestamp Tweaker Tool

## Overview

This program applies a time translation and/or time-scale factor to the timestamps in SubRip subtitle files (.srt format).
The time translation (forward or backward shift) should be given as an int
representing milliseconds. Negative values are supported.

The speed value represents how much faster you want the subtitles to be. This value should be given as a float. The reciprocal of this value will be used as a scaling factor to dilate/contract all timestamps.

It is expected that all timestamps are like this (standard SubRip format):

`00:01:43,108 --> 00:01:44,796`

## Usage

Download the script and run it with:

```bash
python subttt.py srtfile [--speed s] [--offset o] [--replace] [--fix0sec]
```

Accepted options: 

```
positional arguments:
  srtfile          .srt subtitle file (str)
optional arguments:
  -h, --help       show this help message and exit
  --speed SPEED    multiplicative time-scale factor (float); 1.0 is regular
                   speed, 2.0 is doubly fast.
  --offset OFFSET  additive time-offset factor in ms (int); 0 means no offset;
                   accepts negative values
  --replace        replace the original file
  --fix0sec        fix 0-second duration lines
  --debug          enable debug messages
  --version, -v    print version information
```

## TODO

* GUI
* Binaries for Windows.
