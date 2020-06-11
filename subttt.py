#!/usr/bin/env python3

import re
import sys
import os
import math

arrow = "-->"
regexor = "|"
valid_options = ["--replace", "--fix0sec", "--version"]
encoding_list = ["utf_8", "utf_16", "cp65001","utf8-ignore", "ascii", "gb2312", "iso2022_jp", "euc_kr", "latin_1", "iso8859_2", "iso8859_3", "iso8859_4", "iso8859_5", "iso8859_6", "iso8859_7", "iso8859_8", "iso8859_9", "iso8859_10", "iso8859_11", "iso8859_12", "iso8859_13", "iso8859_14", "iso8859_15", "iso8859_16"]

fn_and_delay=[]
options=[]

#Should options be a dictionary/set?
###TODO: verify if we need to work with bytes or if this gizmo is comprehensive enough
###TODO: compatibility with other formats


def sgn(x):
    if x >= 0:
        return 1
    else:
        return -1
    
class Time:
    def __init__(self, *args): #hours, minutes, seconds, milliseconds
        if len(args) == 4:
            hour, min, sec, ms = args
            
            self.hour = hour
            self.min = min
            self.sec = sec
            self.ms = ms
            
        elif len(args) == 1:
            sec = float(args[0])
            
            ms = int(math.fabs(sec*1000))
            sign = sgn(sec)
            ms = int(ms)
            assert sign == 1 or sign == -1, "Sign wasn't determined properly."
            
            self.hour = sign * (ms // (60*60*1000))
            ms = ms % (60*60*1000)
            self.min = sign * (ms // (60*1000))
            ms = ms % (60*1000)
            self.sec = sign * (ms // 1000)
            ms = ms % 1000
            self.ms = sign * ms
            
        elif len(args) == 0:
            self.hour = 0
            self.min = 0
            self.sec = 0
            self.ms = 0
            
        else:
            raise ValueError("Incorrect number of arguments for Time.")
        
    def __repr__(self) -> str:
        return \
            str(self.hour).zfill(2)+":"+\
            str(self.min).zfill(2)+":"+\
            str(self.sec).zfill(2)+","+\
            str(self.ms).zfill(3)
        
    def __int__(self) -> int:
        return self.ms + self.sec*1000 + self.min*60*1000 + self.hour*60*60*1000
    def to_ms(self) -> int:
        return self.__int__()
        
    def __add__(self, value):
        new = Time()
        
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
        assert self.hour+value.hour + oldcarry >= 0, "Underflow while adding hours." 
        
        assert int(self)+int(value) == int(new), "Millisecond sum does not match up."
        return new 

def fix(coisa: str, delay: Time) -> str:
    timesraw = coisa.split(arrow)
    assert len(timesraw) == 2, "list of times has the wrong size; detection failure"
    times=[]
    
    #Create list of Time objects from raw string.
    for timeraw in timesraw:
        hourminsecms = re.split(":"+regexor+",", timeraw)
        times.append( Time( *[int(item) for item in hourminsecms]) )
    
    #Turn 0s subtitles into 1s subtitles.
    if "--fix0sec" in options:
        if times[0].to_ms() == times[1].to_ms():
            if "*" in coisa:
                print("got here!")
            times[1] += Time(0, 0, 1, 0)
    
    #Add delay to time, turn into str and join with arrow.
    return (" "+arrow+" ").join([str(time+delay) for time in times])+"\n"

def usage():
    print("""subTTT: Subtitle Timestamp Tweaker Tool v0.9

This program applies a time translation to the timestamps in SubRip subtitle 
files (.srt format).
The time translation (forward or backward shift) should be given as a float
and in seconds. Minus signs are interpreted as a backward shift (so the 
subtitles will be shown earlier than before).
        
Usage: python subttt.py [OPTION]... SRTFILE SHIFT
  -h, --help                 display this help and exit
  -v, --version              output version information and exit
      --replace              replace the original file\n""")
    
def test(argv: list):
    global fn_and_delay, options, right_enc, right_eh
    
    if len(sys.argv) < 3:
        print("Insufficient arguments.")
        usage()
        exit(1)
    
    for elem in argv[1:]:
        if elem[:2] == "--":
            if elem in valid_options:
                options.append(elem)
            else:
                print(f"Invalid option {elem} .")
                usage()
                exit(1)
        else:
            fn_and_delay.append(elem)
    
    print("fn and delay:", fn_and_delay) ###debug
    print("options:", options) ###debug
    
    if len(fn_and_delay) != 2:
        print("Incorrect arguments.")
        usage()
        exit(1)
        
    filename = fn_and_delay[0]
    delay = fn_and_delay[1]
    
    try:
        float(delay)
        if not math.isfinite(float(delay)):
            raise ValueError("Non-finite float")
    except:
        print(f"Invalid delay {delay}. It must be a finite float.")
        usage()
        exit(1)
    
    try:
        with open(filename, "r") as f:
            pass
    except:
        print(f"Couldn't open {filename}\nCheck file permissions.")
        exit(1)
    
    try:
        with open(filename+"NEW", "w") as f:
            pass
        os.remove(filename+"NEW")
    except:
        print("No write permissions. Check folder permissions.")
        exit(1)
        
    with open(filename,"rb") as f:
        x = f.read()
        
        for enc in encoding_list:
            print(f"Trying to decode with {enc} ...")
            
            #Check for the error handling option.
            error_handling = "strict"
            if "-ignore" in enc:
                enc.replace("-ignore", "")
                error_handling = "ignore"
            
            try:
                s = x.decode(encoding = enc, errors = error_handling)
            except:
                pass
            else: #If no exception occurs.
                right_enc = enc
                right_eh = error_handling
                break
        else: #If the loop finishes without breaking.
            print("Couldn't find a suitable encoding.\nIs the file a valid subtitle file?")
            exit(1)
    
def main():
    if ("--version" in sys.argv) or ("-v" in sys.argv):
        print("\nsubTTT: Subtitle Timestamp Tweaker Tool v0.9")
        exit(0)
    if ("--help" in sys.argv) or ("-h" in sys.argv):
        usage()
        exit(0)
        
    #Verify if something's wrong.
    test(sys.argv) 
    
    #Fetch filename and delay.
    filename = fn_and_delay[0]
    delay = Time(fn_and_delay[1])
    
    #Decode the subtitle file.
    with open(filename, "rb") as f:
        x = f.read()
    s = x.decode(encoding = right_enc, errors = right_eh)
    
    #Name the output file
    if "--replace" not in options:
        dotsplit = filename.split(".")
        if len(dotsplit) >= 2 and len(dotsplit[-1]) <= 3:
            filename = ".".join(dotsplit[:-1]) + "NEW." + dotsplit[-1]
        else:
            filename = filename+"NEW"
            
    #Do the time tweaking.
    with open(filename, "w", encoding = right_enc, errors = right_eh) as newf:
        #Note: Adding too many \r or \n will break everything (maybe?).
        #More testing needs to be done.
        
        for line in s.split("\n"):
            try:
                if arrow in line:
                    try:
                        newf.write(fix(line, delay).strip()+"\r\n")
                    except AssertionError as AE:
                        print("Assertion failed here:",line)
                        print("error: "+AE.args+"\n")
                        newf.write(line+"\n") # hopefully this won't break anything
                else:
                    newf.write(line+"\n")
                    
            except UnicodeDecodeError:
                print("UnicodeDecodeError\nThis shouldn't happen.")
                break

main()