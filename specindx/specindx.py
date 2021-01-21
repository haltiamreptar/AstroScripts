#!/usr/bin/env python


"""
    specindx.py -- makes spectral index maps from data

    Files to use in specindx map, MWA leave as fits for special processing,
    everything else import into miriad, must be image with units JY/Beam, if
    not freq/stokes planed then stash the obs freq in the "restfreq" header
    item order is not important, as long as freqs are there.


Files shouild be a list of quoted file names separated by commas:
files = ["f1", "f2", "f3"]

not a quoted comma seperated list:

files = ["f1, f2, f3"]
"""

files = [
    "snr-askap.mir",
    "snr.2100.linmos",
    "snr.5500.linmos",
    "snr.9000.linmos"
]

# There are no user servicable parts below this line

import os
import math
from operator import itemgetter

# Utilities


def load_mwa(f):
    """ Load MWA gleam image
    expects file name like:
    gleam_cutout_072-103MHz_133_-46333_STACKED.fits

    adds magic to allow miriad to properly process them
    image units, image type, and stashes the obs center freq in the
    restfreq variable"""

    mir = '.'.join(f.split('.')[0:-1])+".mwa"
    #print(mir)
    cmd = "fits in=%s out=%s op=xyin >/dev/null 2>/dev/null"%(f,mir)
    os.system(cmd)
    f1 = float(f.split('_')[2].split('-')[0])
    f2 = float(f.split('_')[2].split('-')[1].split('M')[0])
    freq = 1e-3*(f1+f2)/2
    cmd = "puthd in=%s/bunit value=JY/BEAM >/dev/null"%(mir)
    os.system(cmd)
    cmd = "puthd in=%s/btype value=intensity >/dev/null"%(mir)
    os.system(cmd)
    cmd = "puthd in=%s/restfreq value=%f >/dev/null"%(mir,freq)
    os.system(cmd)
    #print(f1,f2,freq)
    return mir

def get_res_details(f):
    """ extracts bmaj, bmin, bpa and coordinate increment"""
    cmd = "prthd in=%s 2>/dev/null"%(f)
    pcmd = os.popen(cmd)
    output = pcmd.read()
    output = output.split('\n')
    #print(output)
    for lin in output:
        if 'Beam Size' in lin:
            print(lin)
            bmaj = float(lin.split()[2])
            bmin = float(lin.split()[4])
        if 'Position ang' in lin:
            print(lin.split())
            bpa = float(lin.split()[2])
        if lin.startswith("RA"):
            inc = math.fabs(float(lin.split()[4]))
    return bmaj,bmin,bpa,inc

def get_freq(f):
    """ gets image obsrvation frequency, either from the reference pix of
    the frequency axis, or if not available then the restfreq image item """
    cmd = "prthd in=%s"%(f)
    pcmd = os.popen(cmd)
    output = pcmd.read()
    print(output)
    if "FREQ-LSR" in output:
        output = output.split('FREQ-LSR')[1].split()[1]
    elif "FREQ" in output:
        output = output.split('FREQ')[1].split()[1]
    elif "SPECLNMF" in output:
        # Freaking meerkat with its weird lables!
        output = output.split('SPECLNMF')[1].split()[1]
    else:
        cmd = "gethd in=%s/restfreq 2>/dev/null"%f
        pcmd = os.popen(cmd)
        output = pcmd.read()
        #output=output.split('\n')
        #print(output)
        #freq=float(output[10].split()[1])
        #print "TRC=%d,%d"%(self.topx,self.topy)
    return float(output)
def get_sig(f):
    cmd = "sigest in=%s 2>/dev/null"%f
    pcmd = os.popen(cmd)
    output = pcmd.read()
    output = output.split('\n')
    for lin in output:
        if 'Estim' in lin:
            return float(lin.split()[-1])
def do_log(f):
    cmd = "maths exp='log(<%s>)' mask='<%s>.gt.%e' out=%s.log 2>/dev/null >/dev/null"%(f,f,0,f)
    os.system(cmd)

def doSy(files,sig2):
    cmd = "maths exp='"
    for v in zip(files,sig2):
        cmd += "+(<%s.log>/%e)"%v

    cmd += "' out=Sy"# 2>/dev/null >/dev/null"
    print(cmd)
    os.system(cmd)

def doSxy(files,freq,sig2):
    cmd = "maths exp='"
    for v in zip(freq,files,sig2):
        cmd += "+(%e*<%s.log>/%e)"%v
    cmd += "' out=Sxy "
    print (cmd)
    os.system(cmd)


def doB(delta,Sx,S):
    cmd = "maths exp='(%e*<Sxy>-<Sy>*(%e))/%e' out=specindx.mir "%(S,Sx,delta)
    print (cmd)
    os.system(cmd)
""" End utilities """

""" Get file details """
res = []
freq = []
sig = []
sig2 = []


for f in files:
    print("Processing %s"%f)
    if f.endswith('fits'):
        newf = load_mwa(f)
        infiles[infiles.index(f)] = newf
        f = newf
    res.append(get_res_details(f))
    freq.append(math.log(get_freq(f)))
    sig.append(math.log(get_sig(f)))

print ("files=",files)
print ("res=",res)
print ("freq=",freq)
""" find finest pixel grid """
finest = res.index(min(res,key=itemgetter(3)))
print(finest)
""" regrid images to this pixel grid """
for i in range(len(files)):
    if i == finest:
        continue
    cmd = "regrid in=%s tin=%s axes=1,2 out=%s >/dev/null 2>/dev/null"%(files[i],files[finest],files[i]+'.rg')
    #print(cmd)
    os.system(cmd)
    files[i] = files[i]+'.rg'


""" find biggest beam """
biggest = res.index(max(res,key=itemgetter(0)))
""" convolve to same resolution """
for i in range(len(files)):
    if i == biggest:
        continue
    cmd = "convol fwhm=%e,%e pa=%e map=%s out=%s options=final >/dev/null 2>/dev/null"%(res[biggest][0],res[biggest][1],res[biggest][3],files[i],files[i]+'.convol')
    #print(cmd)
    files[i] = files[i]+'.convol'
    os.system(cmd)
print(res,biggest)

print(files)
print(res[biggest])

""" rename the files to something short so maths doesnt blow up! """
for f in range(len(files)):
    os.rename(files[f],"f%02d"%(f))
    files[f] = "f%02d"%(f)

""" log the matched files """
for f in files:
    do_log(f)

""" do the fit """
sig2=[ a*a for a in sig]
#print(freq,sig,sig2,files)
S=sum([1/s2 for s2 in sig2])
Sx=sum([f/s2 for f,s2 in zip(freq,sig2)])
Sxx=sum([f*f/s2 for f,s2 in zip(freq,sig2)])
delta=S*Sxx -(Sx*Sx)
print(S,Sx,Sxx,delta)

doSy(files,sig2)

doSxy(files,freq,sig2)
doB(delta,Sx,S)
""" Fix the Units in the spectral index map """
cmd = "puthd in=specindx.mir/btype value=spectral_index >/dev/null"
os.system(cmd)
cmd = "puthd in=specindx.mir/bunit value='SpectralIndex' >/dev/null"
os.system(cmd)



for f in files:
    os.system("rm -rf %s.log"%f)
os.system("rm -rf *.mwa*")
os.system("rm -rf *.rg*")
os.system("rm -rf f0*")
os.system("rm -rf Sy")
os.system("rm -rf Sxy")


exit()


