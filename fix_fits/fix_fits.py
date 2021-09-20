#!/usr/bin/env python3
"""fix_fits.py

A script to modify fits files, for various use cases.

Only operates on the first HDU, others will be silently dropped.

Usage:
    fix_fits.py drop INPUT [ -o FILE ]
    fix_fits.py beam INPUT [ -o FILE ] BMAJ BMIN  BPA


Options:
    -h --help  Show this message.
    -o FILE  if not specified then name is input-command.fits
    -v --version  Display version information


Units for BMAJ BMIN etc can be specified with a , eg 45,arcsec
BMAJ and BMIN default to arcsec, BPA degrees.
"""


__author__="Dr Evan Crawford (e.crawford@westernsydeny.edu.au)"
__version__="0.4"

from docopt import docopt
import sys
import os
import re

import astropy.io.fits as f
import astropy.wcs as w
import astropy.units as u
import numpy as np

stokes=['','I','Q','U','V']

def extract_unit_value(s,unt):
    """Extracts a value/unit from a string of the form nnn,uuu
       u is  used if no unit found
    """
    if ',' in s:
        v=float(s.split(',')[0])
        unt=u.Unit(s.split(',')[1])
    else:
        v=float(s)

    return v * unt




def beam(input,output,BMAJ,BMIN,BPA):
    inp=f.open(input)
    inp[0].header['bmaj']=BMAJ.to(u.deg).value
    inp[0].header['bmin']=BMIN.to(u.deg).value
    inp[0].header['bpa']=BPA.to(u.deg).value
    inp.writeto(output)

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
    ### Check for extra headers to copy over!
    ## The regex is the ones WCS will deal with!
    r=re.compile("SIMPLE|BITPIX|NAXIS\d*|EXTEND|WCSAXES|CRPIX\d+|CDELT\d+|CUNIT\d+|CTYPE\d+|CRVAL\d+|PV\d+_\d+|CD\d+_\d+|LONPOLE|LATPOLE|CNAME\d+")
    for k in inp.header:
        if not r.match(k):
            out.header[k]=inp.header[k]




    out.header['HISTORY']="fits file updated by: " + __file__ + " " + __version__
    out.header["HISTORY"]="command: " + ' '.join(sys.argv)
    ## stash old value in HISTORY for issue #1
    # find stokes axis
    try:
        stokesAx=list(wcs.wcs.ctype).index('STOKES')
        # from miriad
        #ipol = nint(crval + cdelt*(j-crpix))
        ipol=int(wcs.wcs.crval[stokesAx] +
                 wcs.wcs.cdelt[stokesAx] * (inp.data.shape[len(inp.data.shape)-stokesAx-1]-wcs.wcs.crpix[stokesAx]))
        out.header["HISTORY"]="OLD STOKES: " + stokes[ipol]
    except ValueError:
        print("No stokes axis to stash")
    try:
        stokesAx=list(wcs.wcs.ctype).index('FREQ')
        print(stokesAx)
        # from miriad
        #ipol = nint(crval + cdelt*(j-crpix))
        ipol=(wcs.wcs.crval[stokesAx] +
                 wcs.wcs.cdelt[stokesAx] * (inp.data.shape[len(inp.data.shape)-stokesAx-1]-wcs.wcs.crpix[stokesAx]))
        print(ipol)

        out.header["HISTORY"]="OLD FREQ: %g" % ipol
        out.header['RESTFREQ']=ipol
    except ValueError:
        print("No stokes axis to stash")
    # write it out
    out.writeto(output)



if __name__ == "__main__":

    ## Grab docopt arguments
    arguments=docopt(__doc__,version="%s -- %s"%(__file__,__version__))
    #print(arguments)
    # make a decision not sure I like this yet, need to add extra commands
    # to see if its bad
    if arguments['drop']:
        command='drop'
    elif arguments['beam']:
        command='beam'


    if arguments['-o']:
        output=arguments['-o']
    else:
        output='.'.join(os.path.basename(arguments['INPUT']).split('.')[:-1])+'-'+command+'.fits'
    print(output)
    if arguments['drop']:
        drop(arguments['INPUT'],output)
    if arguments['beam']:
        bmaj=extract_unit_value(arguments['BMAJ'],u.arcsec)
        bmin=extract_unit_value(arguments['BMIN'],u.arcsec)
        bpa=extract_unit_value(arguments['BPA'],u.deg)
        beam(arguments['INPUT'],output,bmaj,bmin,bpa)
