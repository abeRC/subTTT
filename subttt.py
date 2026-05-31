#!/usr/bin/env python3

"""Python script to scale (speed up / slow down) and offset (delay / advance) .srt subtitles."""

from __future__ import annotations # required by python 3.7
import re
import sys
import os
import math
import argparse
import logging
from typing import Tuple, Union, Optional # required by python 3.7

PROGRAM_NAME = "subTTT (Subtitle Timestamp Tweaker Tool) "
PROGRAM_VERSION = "v1.0"
EPILOG = PROGRAM_NAME + " " + PROGRAM_VERSION + " -- Copyright (c) abeRC"
arrow_char = "-->"
regex_pattern = r"([0-9]+)"
newline_char = "\n"

def sgn(x):
    if x >= 0:
        return 1
    else:
        return -1
def log_debug (*args):
    logging.debug("".join([str(x) for x in args]))
def log_info (*args):
    logging.info("".join([str(x) for x in args]))
    
class Timestamp:
    """Class used to represent timestamps (hours, minutes, seconds, milliseconds) in .srt files.
    If only 1 argument is given, it is assumed to represent milliseconds."""
    def __init__(self, *args : Optional[Union[int, Tuple[int,int,int,int]]]): #hours, minutes, seconds, milliseconds
        if len(args) == 4:
            hour, mins, sec, ms = args
            
            self.hour = int(hour)
            self.min = int(mins)
            self.sec = int(sec)
            self.ms = int(ms)
            
        elif len(args) == 1: # value given assumed to be in ms
            ms = int(args[0]) # coerce into int!
            sign = sgn(ms)
            ms = abs(ms)
            
            self.hour = sign * (ms // (60*60*1000))
            ms = ms % (60*60*1000)
            self.min = sign * (ms // (60*1000))
            ms = ms % (60*1000)
            self.sec = sign * (ms // 1000)
            ms = ms % 1000
            self.ms = sign * ms

        # empty object
        elif len(args) == 0:
            self.hour = 0
            self.min = 0
            self.sec = 0
            self.ms = 0
            
        else:
            raise ValueError("Incorrect number of arguments for Time.")
        
    def __repr__(self) -> str:
        return \
            str(abs(self.hour)).zfill(2)+":"+\
            str(abs(self.min)).zfill(2)+":"+\
            str(abs(self.sec)).zfill(2)+","+\
            str(abs(self.ms)).zfill(3)
        
    def __int__(self) -> int:
        return self.ms + self.sec*1000 + self.min*60*1000 + self.hour*60*60*1000
    def to_ms(self) -> int:
        """Return equivalent time in milliseconds."""
        return self.__int__()
    
    def __eq__(self, value):
        return self.to_ms() == value.to_ms()
        
    def __add__(self, value : Union[Timestamp,int]):
        if int(self) + int(value) < 0:
            raise ValueError("Addition error: timestamp result is negative")
        value = Timestamp(value)
        new = Timestamp()
        
        oldcarry = (self.ms+value.ms) // 1000
        carry = oldcarry
        new.ms = (self.ms+value.ms) % 1000
        
        carry = (self.sec+value.sec + carry)//60
        new.sec = (self.sec+value.sec + oldcarry) % 60
        oldcarry = carry
        
        carry = (self.min+value.min + carry)//60
        new.min = (self.min+value.min + oldcarry) % 60
        oldcarry = carry
        
        carry = (self.hour+value.hour + carry)//60
        new.hour = (self.hour+value.hour + oldcarry) % 60
        return new 

    def scale(self, scale_factor : float):
        """Return timestamp scaled (multiplied) by the given factor."""
        return Timestamp(self.to_ms() * scale_factor)

    def list_components(self) -> Tuple[int, int, int, int]:
        """Return a tuple of (hour, min, sec, ms)."""
        return self.hour, self.min, self.sec, self.ms

def fix(line: str, line_index: int, offset: int, speed: float, fix0sec: bool = False) -> str:
    """Takes a str representing a line in the subrip format and performs a linear transformation on the timestamps, 
    i.e. (timestamp1+offset)*1/speed """

    # line looks like this: "00:00:03,190 --> 00:00:06,270\n", so there should be 8 numbers + 9 possible separator components
    # Quoting from the docs:
    # "If there are capturing groups in the separator and it matches at the start of the string, 
    # the result will start with an empty string. The same holds for the end of the string
    # That way, separator components are always found at the same relative indices within the result list."
    # This guarantees 17 components. 
    line_components = re.split(regex_pattern, line)
    if len(line_components) != 17 or arrow_char not in line:
        raise ValueError(f"Possible malformed line at index {line_index}. Please correct your subtitle file.\n{line_index}: {line}")
    
    # Create list of Timestamp objects from raw string.
    # ['', '00', '', '00', '', '03', '', '190', ' --> ', '00', '', '00', '', '06', '', '270', '\n']
    timestamp1_comps, timestamp2_comps, sep_comps = [], [], []
    for i, component in enumerate(line_components):
        try:
            if i < 9: # first timestamp
                timestamp1_comps.append(int(component))
            else: # second timestamp
                timestamp2_comps.append(int(component))
        except ValueError: # separator component
            sep_comps.append(component)
    timestamp1, timestamp2 = Timestamp(*timestamp1_comps), Timestamp(*timestamp2_comps)

    #Turn 0s subtitles into 1s subtitles.
    if fix0sec:
        if timestamp1 == timestamp2:
            log_info(f"Fixing 0-second line at index {line_index}")
            timestamp2 += Timestamp(0, 0, 1, 0)
    
    # Add offset and multiply by 1/speed
    assert speed > 0
    timestamp1, timestamp2 = (timestamp1+offset).scale(1/speed), (timestamp2+offset).scale(1/speed)

    # combine everything together (initial and final whitespaces, timestamps and arrow)
    result = sep_comps[0] + str(timestamp1) + sep_comps[4] + str(timestamp2) + sep_comps[-1]
    return result

def setup_logging(debug: bool):
    """Setup logging. By default, logging level is INFO but can be set to DEBUG via command-line option."""
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    log_format = "[{levelname}] - {message}"
    logging.basicConfig(level=log_level, format=log_format, style="{")

def parse_arguments():
    """Parse command-line arguments using the argparse library."""

    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG
    )
    # positional and takes a single value
    parser.add_argument(
        "srtfile",
        type=str,
        help=".srt subtitle file (str)"
    )
    # optional and takes a single value
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="multiplicative time-scale factor (float); 1.0 is regular speed, 2.0 is doubly fast."
    )
    # optional and takes a single value
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="additive time-offset factor in ms (int); 0 means no offset; accepts negative values"
    )
    # on/off flag; default is false
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace the original file",
    )  
    # on/off flag; default is false
    parser.add_argument(
        "--fix0sec",
        action="store_true",
        help="fix 0-second duration lines",
    )  
    # on/off flag; default is false
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="enable debug messages"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=EPILOG,
        help="print version information",
    )
    args = parser.parse_args()
    return args

def verify_initial(args : argparse.Namespace):    
    # utf8-replace is utf8 encoding with the 'replace' error handling option
    possible_encodings = ["utf_8", "utf_16", "cp65001","utf8-replace", "ascii", "gb2312", "iso2022_jp", "euc_kr", "latin_1", "iso8859_2", "iso8859_3", 
        "iso8859_4", "iso8859_5", "iso8859_6", "iso8859_7", "iso8859_8", "iso8859_9", "iso8859_10", "iso8859_11", "iso8859_12", "iso8859_13", 
        "iso8859_14", "iso8859_15", "iso8859_16"]
    right_enc, right_error_handling = None, None
    srtfile, offset, speed = args.srtfile, args.offset, args.speed
    
    # refuse infinite floats
    if not math.isfinite(offset) or not math.isfinite(speed):
        raise ValueError(f"Invalid offset {offset}. It must be a finite float.")

    # check if speed is reasonable
    if speed <= 0:
        raise ValueError(f"Invalid time-speed factor {speed}. It must be a positive float.")
    if speed < 0.2 or speed > 5:
        logging.warning(f"Time-scale factor {speed} is too small or too large. It should not be a percentage. Consider the default (no action) is 1.0.")
    if speed == 1.0 and offset == 0:
        logging.warning("Both speed and offset are unchanged from default.")

    # refuse invalid paths
    try:
        with open(srtfile, "r") as f:
            pass
    except:
        raise OSError(f"Couldn't open {srtfile}. Check file path and permissions.")

    # check extension
    if not srtfile.lower().endswith(".srt"):
        logging.warning("Subtitle file does not have the .srt extension.")

    # check for file creating permissions
    try:
        with open(srtfile+"mod", "w") as f:
            pass
        os.remove(srtfile+"mod")
    except:
        raise OSError("Couldn't write file. Check folder permissions.")
    
    # check encoding
    with open(srtfile,"rb") as f:
        x = f.read()
        
        for enc in possible_encodings:
            log_info(f"Trying to decode with {enc} ...")
            
            #Check for the error handling option.
            error_handling = "strict"
            if "-replace" in enc:
                enc.replace("-replace", "")
                error_handling = "replace"
            
            try:
                s = x.decode(encoding = enc, errors = error_handling)
            except:
                pass
            else: #If no exception occurs.
                right_encoding = enc
                right_error_handling = error_handling
                break
        else: #If the loop finishes without breaking.
            raise OSError("Couldn't find a suitable encoding.\nIs the file a valid .srt file?")

        if arrow_char not in s:
            logging.error(f"Couldn't find the string '-->' in {srtfile}. Is it a valid .srt file?\nParsing cannot continue...")
            exit(1)
    return right_encoding, right_error_handling
    
def main():
    args = parse_arguments() # parse command-line arguments
    setup_logging(args.debug)
    log_info(str(args))

    # Verify if something's wrong.
    right_encoding, right_error_handling = verify_initial(args) 

    # Assign arguments into variables
    srtfile, offset, speed = args.srtfile, args.offset, args.speed
    
    # Decode the subtitle file. newline='' guarantees original newlines are preserved.
    with open(srtfile, "r", encoding=right_encoding, errors=right_error_handling, newline='') as f:
        lines = f.readlines()
    
    # Name the output file
    if not args.replace:
        dotsplit = srtfile.split(".")
        if len(dotsplit) >= 2 and len(dotsplit[-1]) <= 3: # check if the thing after the dot is likely an extension
            srtfile = ".".join(dotsplit[:-1]) + "_mod." + dotsplit[-1]
        else:
            srtfile = srtfile+"_mod"
            
    # Do the time tweaking.
    to_write = ""
    for i, line in enumerate(lines):
        if arrow_char in line:
            to_write += fix(line, i, offset, speed, fix0sec=args.fix0sec)
        else:
            to_write += line

    # Write the resulting file to disk. newline='' guarantees original newlines are preserved.
    with open(srtfile, "w", encoding = right_encoding, errors = right_error_handling, newline='') as newf:
        newf.write(to_write)
    log_info(f"Finished! Output written into {srtfile}")
main()