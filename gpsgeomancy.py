#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""gpsgeomancy.py
2015/02/05 14:29:53

An attempt to help Martin with his GPS geomancy idea.

Take an attached GPS (serial) and get the satellite positions and
data from the NMEA GSV sentences. Find four suitable data sets
(satellites) that correspond to the cardinal directions (North,
South, East, West) and return their data.

Geomantic divination information from Stephen Skinner "Terrestrial
Astronomy - Divination by Geomancy" (the asterisks are the
'reading' - they can be two dots or one):

      Earth    Water    Air     Fire
       IV       III     II       I
head   **        *      **       *
neck   **        *      **       *
body   *         *      *        **
feet   *         **     **       **
      West     North    East    South

Suggested correspondence between these categories and the GPS data
from the NMEA sentences. The satellites corresponding to the
cardinal points / elements are chosen by their closeness to the
azimuths (N=0, E=90, S=180, W=270) and then their signal to noise
(SNR) and then if necessary their elevation (closer to 45 wins?)

      West     North    East    South
prn    **        *      **       *
ele    **        *      **       *
azi    *         *      *        **
snr    *         **     **       **

Two stars could be even numbers, one star odd.

The default location of the GPS is /dev/ttyUSB0 but you can change
this with the -p (--port) option. The default baud rate for the GPS
is 4800 but you can change this with the -b (--baud) option. Garmin
etrex and similar tend to be on ttyUSB0 at 4800 but the dataloggers
can be on ttyACM0 and they are all 115200 baud.

Copyright 2015 Daniel Belasco Rogers danbelasco@yahoo.co.uk

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301 USA.
"""

import sys
import argparse
from pprint import pprint
try:
    import serial
except ImportError:
    print """Please install pySerial:
sudo apt-get install python-serial"""
    sys.exit(2)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Geomancy with GPS satellite positions')
    parser.add_argument('-b', '--baud',
                        help="Set the baud rate for the GPS. Default is 4800",
                        default=4800)
    parser.add_argument('-p', '--port',
                        help="Address of the GPS. Default is /dev/ttyUSB0",
                        default="/dev/ttyUSB0")
    return parser.parse_args()


def connectgps(port, baud):
    try:
        gps = serial.Serial(port, baud, timeout=1)
    except serial.SerialException:
        print """
Could not open port %s,
is the GPS plugged in and turned on?
""" % port
        sys.exit(2)
    return gps


def checksum(data):
    """
    checksum(data) -> str Internal method which calculates
    the XOR checksum over the sentence (as a string, not including
    the leading '$' or the final 3 characters, the ',' and
    checksum itself).
    """
    checksum = 0
    for character in data:
        checksum = checksum ^ ord(character)
        hex_checksum = "%02x" % checksum
    return hex_checksum.upper()


def formatline(line):
    """
    preformatting on all NMEA sentences. Returns a list of values
    without checksum and without carriage returns
    """
    line.strip()

    # lose carriage returns
    if line.endswith('\r\n'):
        line = line[:len(line) - 2]

    # validate
    star = line.rfind('*')
    if star >= 0:
        check = line[star + 1:]
        line = line[1:star]
        sum = checksum(line)
        if sum != check:
            print "failed checksum"
            return None
    else:
        print "no checksum"
        return None

    # lose checksum now we've validated it
    line = line[2:]

    # create a list of all elements in sentence
    line = line.split(',')
    return line


def parseGSV(line, gps):
    """

    only interested in gsv sentences, otherwise just return none to
    calling function

    $GPGSV,3,1,12,01,80,283,20,32,77,227,18,11,72,175,19,20,42,247,25*79
    $GPGSV,3,2,12,14,35,055,15,19,23,174,28,17,19,318,26,28,15,281,15*7C
    $GPGSV,3,3,12,22,11,068,17,23,05,194,,31,04,113,,36,,,*4A

    """
    gsvlist = [line]
    num_of_sentences = int(line[1])
    print "sentences: %d\tsatellites: %s" % (num_of_sentences, line[3])

    # number of GSV sentences vary. Fetch them all before
    # parsing the values
    for sentence in range(num_of_sentences - 1):
        line = gps.readline()
        line = formatline(line)
        gsvlist.append(line)

    return gsvlist


def formatgsvlist(gsvlist):
    """
    """

    formattedgsv = []

    for sentence in gsvlist:

        # ignore first 4 items (This is the header, number of
        # sentences, sentence number and number of satellites and
        # so not necessary for us at this point)
        sentence = sentence[4:]

        # Replace empty fields with 0 if there is no data
        for item in sentence:
            if item == '':
                item = 0
            formattedgsv.append(int(item))

    return formattedgsv


def makesatdict(gsvlist):
    """
    makes a dictionary with prn as a key and values as a list e.g.
    prn:[ele, azi, snr]
    """
    satdict = {}

    for item in range(0, len(gsvlist), 4):
        satdict[gsvlist[item]] = [gsvlist[item + 1],
                                  gsvlist[item + 2],
                                  gsvlist[item + 3]]

    return satdict


def directionclassify(satdict):
    """Appends compass direction onto end of list for each satellite"""
    for prn in satdict:
        azi = satdict[prn][1]
        if azi > 315 or azi < 45:
            satdict[prn].append("North")
        if azi > 45 and azi < 135:
            satdict[prn].append("East")
        if azi > 135 and azi < 225:
            satdict[prn].append("South")
        if azi > 225 and azi < 315:
            satdict[prn].append("West")

    return satdict


def getsatellites(gps):
    """
    main reiterating loop which reads the incoming nmea sentences
    from the gps, sends to parser and catches user interrupt:
    ctrl-c
    """
    gsvlist = []
    while gsvlist == []:
        try:
            line = gps.readline()
            if line.startswith('$GPGSV'):
                line = formatline(line)

                # formatline performs checksum and returns None if
                # it fails
                if line is None:
                    continue

                gsvlist = parseGSV(line, gps)
                gsvlist = formatgsvlist(gsvlist)

            else:
                continue

            return gsvlist

        except KeyboardInterrupt:
            # user sent ctrl-c to stop script
            gps.close()
            print """
user interrupt, shutting down"""
            sys.exit()


def main():
    """
    """
    args = parse_arguments()

    gps = connectgps(args.port, args.baud)

    satellitepositions = getsatellites(gps)

    # sort and filter satellites
    satdict = makesatdict(satellitepositions)

    satdict = directionclassify(satdict)
    pprint(satdict)



    # Prepare 'mothers'


    # Format and print 'mothers' to screen


if __name__ == '__main__':
    sys.exit(main())
