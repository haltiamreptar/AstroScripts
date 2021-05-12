#!/usr/bin/env python
"""fix_fits.py

A script to undo the compression on HDUs as
implemented in the .fz file format.

It will not overwirte an existing file.


Usage:
    fix_fits.py INPUT [ -o OUTPUT ]



Options:
    -h --help  Show this message.
    -o OUTPUT  if not specified then name is INPUT-uncompressed.fits
    -v --version  Display version information

"""


__author__="Dr Evan Crawford (e.crawford@westernsydeny.edu.au)"
__version__="0.1"

from docopt import docopt

from astropy.io import fits
import astropy.wcs as W

if __name__ == "__main__":

    ## Grab docopt arguments
    arguments=docopt(__doc__,version="%s -- %s"%(__file__,__version__))
    #print(arguments)
    if arguments['-o']:
        output=arguments['-o']
    else:
        output='.'.join(os.path.basename(arguments['INPUT']).split('.')[:-1])+'-uncompressed.fits'
    f=fits.open(arguments['INPUT'])
    newf=fits.HDUList()
    newf.append(f[0])
    for h in f[1:]:
        wcs=W.WCS(h.header)
        n=fits.ImageHDU(h.data)
        n.header.update(wcs.to_header())
        newf.append(n)
    newf.writeto(output)