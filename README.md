# gpsgeomancy
An attempt to help Martin Howse with his GPS geomancy idea.

    usage: gpsgeomancy.py [-h] [-v] [-b BAUD] [-p PORT]

    Geomancy with GPS satellite positions

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Print verbose outputs to screen (intermediate selections etc.)
      -b BAUD, --baud BAUD  Set the baud rate for the GPS. Default is 4800
      -p PORT, --port PORT  Address of the GPS. Default is /dev/ttyUSB0

Take an attached GPS (serial) and get the satellite positions and
data from the NMEA GSV sentences. Find four suitable data sets
(satellites) that correspond to the cardinal directions (North,
South, East, West) and return their data.

Geomantic divination information from Stephen Skinner "Terrestrial
Astronomy - Divination by Geomancy" (the asterisks are the
'reading' - they can be two dots or one):

>           Earth    Water    Air     Fire
>            IV       III     II       I
>     head   **        *      **       *
>     neck   **        *      **       *
>     body   *         *      *        **
>     feet   *         **     **       **
>           West     North    East    South

Suggested correspondence between these categories and the GPS data
from the NMEA sentences. The satellites corresponding to the
cardinal points / elements are chosen by their closeness to the
azimuths (N=0, E=90, S=180, W=270) and then their signal to noise
(SNR) and then if necessary their elevation (closer to 45 wins?)

>           West     North    East    South
>     prn    **        *      **       *
>     ele    **        *      **       *
>     azi    *         *      *        **
>     snr    *         **     **       **

Two stars could be even numbers, one star odd.

The default location of the GPS is /dev/ttyUSB0 but you can change
this with the -p (--port) option. The default baud rate for the GPS
is 4800 but you can change this with the -b (--baud) option. Garmin
etrex and similar tend to be on ttyUSB0 at 4800 but the dataloggers
can be on ttyACM0 and they are all 115200 baud.

If you run the script with the -v option, you get to preview some
of the intermediate decisions the script is making.

BUG On my system, /dev already has a ttyUSB0 entry even when
there's nothing plugged in. If you leave the script polling the
default port address, nothing happens - no timeout, no exception,
it just hangs.

Not sure how to catch this and only hope that other users of this
don't have a /dev/ttyUSB0 entry when nothing is plugged in.
