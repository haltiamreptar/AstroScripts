#!/usr/bin/env python3
"""fix_fits.py

A script to modify fits files, for various use cases.

Only operates on the first HDU, others will be silently dropped.

Usage:
    fix_fits.py drop INPUT [ -o FILE ]

Options:
    -h --help  Show this message.
    -o FILE  if not specified then name is input-command.fits
    -v --version  Display version information
"""


__author__="Dr Evan Crawford (e.crawford@westernsydeny.edu.au)"
__version__="0.1"

from docopt import docopt
import sys


import astropy.io.fits as f
import astropy.wcs as w
import numpy as np

def drop(input, output):
    # read in first hdu of fits file
    inp=f.open(input)[0]
    # create a wcs object
    wcs=w.WCS(inp.header)
    # drop the degenerate axes
    d=inp.data.squeeze()
    # build new fits file with data
    out=f.PrimaryHDU(data=d)
    # add just the celestial header back
    out.header.update(wcs.celestial.to_header())
    # write it out
    out.writeto(output)



if __name__ == "__main__":
    arguments=docopt(__doc__,version="%s -- %s"%(__file__,__version__))
    print(arguments)



    if arguments['drop']:
        command='drop'

    if arguments['-o']:
        output=arguments['-o']
    else:
        output='.'.join(arguments['INPUT'].split('.')[:-1])+'-'+command+'.fits'

    if arguments['drop']:
        drop(arguments['INPUT'],output)