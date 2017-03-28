#!/usr/bin/python
# 
# Integrated and modified by Salvador Mendoza (salmg.net)
# March 28, 2017
#
# A combination of cab.py + cmsb.py + dmsb.py from http://alcrypto.co.uk/magstripe/
#  - Create Aiken Biphase 
#  - Create MagStripe Binary
#  - Decode MagStripe Binary
# 
# How to run it:
#
#./MalfunctionMag.py <parameters>
#
#	To encode mag-stripe:
#
#		-t [Track #[1-3]] | default:1>
#		-c <data>
#		-z [# of zeros | default:20] 
#		-s [samples per bit | default:15]
#		-f [wav filename | if not specified, only creates/shows MagStripe Binary code]
#               
#	To decode Magstripe binary:
#		-d [data]
#
# ------------------------------------------------------------------
# Original files statements:
# ------------------------------------------------------------------
#
# cab.py: Create Aiken Biphase
# create a WAV file with arbitrary data in it
#
# Copyright(c) 2006, Major Malfunction <majormal@pirate-radio.org>
# http://www.alcrypto.co.uk
#
# inspired by 'dab.c' by Joseph Battaglia <sephail@sephail.net>
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to
#   deal in the Software without restriction, including without limitation the
#   rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#   sell copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#   IN THE SOFTWARE.
#
# version 0.1:
#	just get the thing working with fixed WAV and other parameters!
# ------------------------------------------------------------------
# cmsb.py: Create MagStripe Binary
# Convert ASCII data to ABA/IATA binary with LRC
# Inspired by dmsb.c by Joseph Battaglia <sephail@sephail.net>
# 
# Copyright 2006,2007 Major Malfunction <majormal@pirate-radio.org>
# version 0.1 (IATA only)
#   http://www.alcrypto.co.uk/
#   Distributed under the terms of the GNU General Public License v2
# version 0.2 (add ABA capability, characterset checking)
#   Parts Copyright 2007 Mansour Moufid <mmoufid@connect.carleton.ca>
# ------------------------------------------------------------------
# dmsb.py: Decode MagStripe Binary
#
# Copyright(c) 2006, 2007, Major Malfunction <majormal@pirate-radio.org>
# http://www.alcrypto.co.uk
#
# based on original 'dmsb.c' by Joseph Battaglia <sephail@sephail.net>
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to
#   deal in the Software without restriction, including without limitation the
#   rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#   sell copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#   IN THE SOFTWARE.
#
# version 0.1:
#	just get the thing working for IATA!
# version 0.2:
#	fix end sentinel search

from wave import open
from struct import pack
from operator import xor
from optparse import OptionParser

bits = 7
base = 32
max = 63
padding = frequency = data = filen = None

def main():
    global bits, base, max, padding, frequency, data, filen
    parser = OptionParser('Usage: \n\t'+ __file__ + ' <parameters>:' +\
      '\n\n\tTo encode mag-stripe:\n\t\t-t [Track #[1-3]] | default:1>' +\
      '\n\t\t-c <data>\n\t\t-z [# of zeros | default:20] '+\
      '\n\t\t-s [samples per bit | default:15]'+\
      '\n\t\t-f [wav filename | if not specified, only shows binary encode]\n\n' +\
      '\n\tTo decode Magstripe binary:\n\t\t-d [data]\n')
    parser.add_option('-t', dest='tr', type='string',\
      help='specify track number')
    parser.add_option('-c', dest='da', type='string',\
      help='data for the track')
    parser.add_option('-z', dest='ze', type='string',\
      help='specify number of leading zeros')
    parser.add_option('-s', dest='sa', type='string',\
      help='Samples per bit, recommended [5-45]')
    parser.add_option('-f', dest='fi', type='string',\
      help='File name')
    parser.add_option('-d', dest='mb', type='string',\
      help='MagStripe Binary')
    (options, args) = parser.parse_args()
    
    trackp = options.tr
    data = options.da
    padding = options.ze
    frequency = options.sa
    filen = options.fi
    
    if options.mb != None:
        decodeMagbinary(options.mb)
    else:
        if data == None:
            print parser.usage
            exit(0)

        padding = int(padding) if padding != None else 20
        frequency = int(frequency) if frequency != None else 15

        if trackp != None:
            if trackp == '2' or trackp == '3':
                bits = 5
                base = 48
                max = 15
                
        GenerateWav()
            
def decodeMagbinary(data):
    # check for IATA data - find start sentinel
    start_decode = data.find("1010001")
    if start_decode < 0:
        print "No start sentinel found!"
        exit(-1)
        
    end_sentinel = data.find("1111100")
    # check end sentinel is on 7 bit boundry
    while (end_sentinel - start_decode) % 7:
        newpos = data[end_sentinel + 1:].find("1111100")
        if newpos >= 0:
            end_sentinel += newpos + 1
        else:
            print "No end sentinel found!"
            exit(-1)
            
    # LRC comes immediately after end sentinel
    actual_lrc = end_sentinel + 7
    # initialise rolling LRC
    rolling_lrc = [0,0,0,0,0,0,0]
    decoded_string = ''
    # do the decode
    while start_decode <= end_sentinel:
        asciichr= 32
        parity= int(data[start_decode + 6])
        
        for x in range(6):
            asciichr += int(data[start_decode + x]) << x
            parity += int(data[start_decode + x])
            rolling_lrc[x]= xor(rolling_lrc[x],int(data[start_decode + x]))
            
        # check parity
        if not parity % 2:
            print "parity error!"
            exit(-1)
            
        decoded_string += chr(asciichr)
        start_decode += 7
        
    # check LRC
    parity = 1
    for x in range(6):
        parity += rolling_lrc[x]
        
    rolling_lrc[6]= parity % 2
    for x in range(7):
        if not rolling_lrc[x] == int(data[actual_lrc + x]):
            print "LRC/CRC check failed!"
            exit(-1)
    print "result:"
    print decoded_string
    
def GenerateWav():
    global data, trackp
    zero = ''
    lrc = []
    output = ''
    for x in range(bits):
        zero += "0"
        lrc.append(0)
    
    for x in range(padding):
        output += zero

    for x in range( len(data) ):
        raw = ord(data[x]) - base
        if raw < 0 or raw > max:
            print 'Illegal character:' , chr(raw+base)
            exit(0)
            
        parity = 1
        for y in range(bits-1):
            output += str(raw >> y & 1)
            parity += raw >> y & 1
            lrc[y] = xor(lrc[y], raw >> y & 1)
            
        output += chr((parity % 2) + ord('0'))

    parity = 1
    for x in range(bits - 1):
        output += chr(lrc[x] + ord('0'))
        parity += lrc[x]
        
    output += chr((parity % 2) + ord('0'))
    for x in range(padding):
        output += zero
    #Finishing first part of the code:
    print output
    
    #Second part:
    if filen == None:
        exit(0)
    else:
        print "Creating wav file: " + filen
        newtrack=open(filen,"w")
        params= (1, 2, 22050, 0L, 'NONE', 'not compressed')
        newtrack.setparams(params)
        data = output

        peak = 32767
        for x in range(20):
            newtrack.writeframes(pack("h",0))

        # write the actual data
        # square wave for now
        n = 0
        writedata = peak
        while n < len(data):
            if data[n] == '1':
                for x in range(2):
                    writedata = -writedata
                    for y in range(frequency/4):
                        newtrack.writeframes(pack("h",writedata))

            if data[n] == '0':
                writedata = -writedata
                for y in range(frequency/2):
                    newtrack.writeframes(pack("h",writedata))
            n = n + 1
        newtrack.close()
        print "Done"
if __name__ == '__main__':
    main()
