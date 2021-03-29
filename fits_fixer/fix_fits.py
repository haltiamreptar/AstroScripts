#!/usr/bin/env python3
"""fix_fits.py

A script to modify fits files, for various use cases.

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

def stuff():
    outf='.'.join(sys.argv[1].split('.')[0:-1])+"-fixed.fits"
    freq=float(sys.argv[2])
    beam=float(sys.argv[3])
    print(f"outf:{outf}\tfreq:{freq}\tbeam:{beam}")

    #exit()
    t1=f.open(sys.argv[1])
    wcs=w.WCS(t1[0].header)
    wcs=w.utils.add_stokes_axis_to_wcs(wcs,0)
    wcs=w.utils.add_stokes_axis_to_wcs(wcs,0)


    wcs.wcs.ctype[0]='FREQ'
    wcs.wcs.cname[0]='FREQ'
    wcs.wcs.cunit[0]='Hz'
    wcs.wcs.crval[0]=freq
    wcs.wcs.crval[1]=0
    wcs=wcs.reorient_celestial_first()

    d=np.expand_dims(np.expand_dims(t1[0].data,0),0)

    newf=f.PrimaryHDU(data=d)
    newf.header.update(wcs.to_header())
    newf.header['bmaj']=beam/3600.
    newf.header['bmin']=beam/3600.
    newf.header['bpa']=0.
    newf.header['bunit']='JY/BEAM'

    newf.writeto(outf)



if __name__ == "__main__":
    arguments=docopt(__doc__,version="%s -- %s"%(__file__,__version__))
    print(arguments)
