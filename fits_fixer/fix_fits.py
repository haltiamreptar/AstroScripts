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
__version__="0.2"

from docopt import docopt
import sys


import astropy.io.fits as f
import astropy.wcs as w
import numpy as np

stokes=['I','Q','U','V']



def drop(input, output):
    """
    Drops the degenrate (i. e. length 1 ) axes from fits files
    generated from casa & miriad


    """
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
    out.header['HISTORY']="fits file updated by: " + __file__ + " " + __version__
    out.header["HISTORY"]="command: " + ' '.join(sys.argv)
    # write it out
    out.writeto(output)



if __name__ == "__main__":

    ## Grab docopt arguments
    arguments=docopt(__doc__,version="%s -- %s"%(__file__,__version__))

    # make a decision not sure I like this yet, need to add extra commands
    # to see if its bad
    if arguments['drop']:
        command='drop'

    if arguments['-o']:
        output=arguments['-o']
    else:
        output='.'.join(arguments['INPUT'].split('.')[:-1])+'-'+command+'.fits'

    if arguments['drop']:
        drop(arguments['INPUT'],output)