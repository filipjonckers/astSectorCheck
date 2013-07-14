#!/usr/bin/python
'''
AstSectorCheck

Dump sector messages from raw Asterix file.
Copyright (c) 2013 Filip Jonckers.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
 
@author: Filip Jonckers
'''
import struct
import sys

# class containing information for one sector message
class SMM:
    def __init__(self):
        self.sac = 0
        self.sic = 0
        self.type = ''
        self.nm = 0
        self.sm = 0
        self.sector = -1
        self.tod = 0
        self.time = ""

# constants
# by default we assume 32 sectors per rotation period
SECTORS = 32
SECTOREMPTY = '.'
SECTORMARKER = 'X'
NORTHMARKER = 'N'

# list with entries for each SMM EMM and SMM0 timestamp
rotation_ = []
tod_ = 0


# parse raw Asterix file
def parseAsterixFile(astfile):
    with open(astfile, 'rb', 16384) as fp:
        header = fp.read(3)
        while len(header) > 0:
            # parse header
            (cat, length) = struct.unpack('>BH', header)
            # read remainder of  this asterix record
            if cat == 2:
                parseSMM02(cat, length, fp.read(length - 3))
            elif cat == 34:
                parseSMM34(cat, length, fp.read(length - 3))
            else:
                # parseSMM(cat, length, fp.read(length - 3))
                fp.read(length - 3)
            # read next asterix header
            header = fp.read(3)

# process a received SMM/EMM sector crossing message
def newSectorCrossing(smm):
    global rotation_
    global tod_
    # check if this is a new rotation period (SMM=0)
    if smm.sector == 0:
        printRotation()
        rotation_ = getNewRotationList()
        rotation_[SECTORS + 1] = smm.time
        if tod_ == 0:
            # no previous SMM0 timestamp avbl
            rotation_[SECTORS + 2] = 0
        else:
            # calculate rotation time
            rotation_[SECTORS + 2] = smm.tod - tod_
        # save timestamp of SMM0
        tod_ = smm.tod
    # is this a north message?
    if smm.nm == 1:
        rotation_[SECTORS] = NORTHMARKER
    elif smm.sm == 1:
        # mark sector as present
        rotation_[smm.sector] = SECTORMARKER


# create new list of sectors (SMM + EMM + timestamp + rotation time)
def getNewRotationList():
    return [SECTOREMPTY] * (SECTORS + 3)

# print rotation information
def printRotation():
    for sector in rotation_:
        print sector,
    print


# unknown asterix cat debug info
def parseSMM(cat, length, data):
    print "cat=%d len=%d FSPEC=%d [%s]" % (cat, length, getFspec(data)[1], toHexString(data))


#######################################
######## ASTERIX CAT 34 parser ########
#######################################
def parseSMM34(cat, length, data):
    MAXOCTETS = 2
    # discard asterix frame header (cat + length)
    length -= 3
    # current position in frame
    index = 0

    while(length > index):
        # extract FSPEC
        (fspec, fspecSize) = getFspec(data, index)
        # shift to the left for full length FSPEC value
        fspec <<= 8 * (MAXOCTETS - fspecSize)
        # jump over the fspec bytes
        index += fspecSize

        # new SMM object
        smm = SMM()

        # UAP iteration
        if(fspec & 0x8000): index = dataItem010(index, data, smm)
        if(fspec & 0x4000): index = dataItem000(index, data, smm)
        if(fspec & 0x2000): index = dataItem030(index, data, smm)
        if(fspec & 0x1000): index = dataItem020(index, data, smm)
        if(fspec & 0x0800): index = dataItem041(index, data, smm)
        if(fspec & 0x0400): index = dataItem050_34(index, data, smm)
        if(fspec & 0x0200): index = dataItem060(index, data, smm)
        if(fspec & 0x0080): index = dataItem070(index, data, smm)
        if(fspec & 0x0040): index = dataItem100(index, data, smm)
        if(fspec & 0x0020): index = dataItem110(index, data, smm)
        if(fspec & 0x0010): index = dataItem120(index, data, smm)
        if(fspec & 0x0008): index = dataItem090(index, data, smm)
        # SPF & RFS not implemented
    
        # logging
        #print "%s cat=%d sac=%d sic=%d type=%s sector=%d [%s]" % (smm.time, cat, smm.sac, smm.sic, smm.type, smm.sector, toHexString(data))
        
        # parse complete sector message
        newSectorCrossing(smm)


#######################################
######## ASTERIX CAT 02 parser ########
#######################################
def parseSMM02(cat, length, data):
    MAXOCTETS = 2
    # discard asterix frame header (cat + length)
    length -= 3
    # current position in frame
    index = 0

    while(length > index):
        # extract FSPEC
        (fspec, fspecSize) = getFspec(data, index)
        # shift to the left for full length FSPEC value
        fspec <<= 8 * (MAXOCTETS - fspecSize)
        # jump over the fspec bytes
        index += fspecSize

        # new SMM object
        smm = SMM()

        # UAP iteration
        if(fspec & 0x8000): index = dataItem010(index, data, smm)
        if(fspec & 0x4000): index = dataItem000(index, data, smm)
        if(fspec & 0x2000): index = dataItem020(index, data, smm)
        if(fspec & 0x1000): index = dataItem030(index, data, smm)
        if(fspec & 0x0800): index = dataItem041(index, data, smm)
        if(fspec & 0x0400): index = dataItem050_02(index, data, smm)
        if(fspec & 0x0200): index = dataItem060(index, data, smm)
        if(fspec & 0x0080): index = dataItem070(index, data, smm)
        if(fspec & 0x0040): index = dataItem100(index, data, smm)
        if(fspec & 0x0020): index = dataItem090(index, data, smm)
        if(fspec & 0x0010): index = dataItem080(index, data, smm)
        # SPF & RFS not implemented
    
        # logging
        #print "%s cat=%d sac=%d sic=%d type=%s sector=%d [%s]" % (smm.time, cat, smm.sac, smm.sic, smm.type, smm.sector, toHexString(data))
        
        # parse complete sector message
        newSectorCrossing(smm)


def dataItem010(index, data, smm):
    (smm.sac, smm.sic) = struct.unpack('>BB', data[index:index + 2])
    return index + 2

def dataItem000(index, data, smm):
    type = struct.unpack('>B', data[index:index + 1])[0]
    # EMM north message
    if(type == 1):
        smm.nm = 1
        smm.type = 'NM'
    # SMM sector message
    elif(type == 2):
        smm.sm = 1
        smm.type = 'SM'
    return index + 1

def dataItem020(index, data, smm):
    sector = struct.unpack('>B', data[index:index + 1])[0]
    smm.sector = sector // 8
    return index + 1

def dataItem030(index, data, smm):
    # add a leading zero byte - we need 4 bytes to unpack to INT
    smm.tod = struct.unpack('>I', '\0' + data[index:index + 3])[0] / 128.0
    h = smm.tod // 3600
    m = (smm.tod - (h * 3600)) // 60
    s = smm.tod - (h * 3600) - (m * 60)
    smm.time = "%02d:%02d:%05.02f" % (h, m, s)
    return index + 3

def dataItem041(index, data, smm):
    return index + 2

def dataItem050_02(index, data, smm):
    octet = struct.unpack('>B', data[index:index + 1])[0]
    subfields = bitcount(octet >> 1)
    index += 1
    while (octet & 1):
        octet = struct.unpack('>B', data[index:index + 1])[0]
        subfields += bitcount(octet >> 1)
        index += 1
    return index + subfields

def dataItem050_34(index, data, smm):
    octet = struct.unpack('>B', data[index:index + 1])[0]
    subfields = bitcount(octet >> 1)
    if octet & 4:
        # MDS field is 2 octets
        subfields += 1
    index += 1
    while (octet & 1):
        octet = struct.unpack('>B', data[index:index + 1])[0]
        subfields += bitcount(octet >> 1)
        index += 1
    return index + subfields

def dataItem060(index, data, smm):
    octet = struct.unpack('>B', data[index:index + 1])[0]
    subfields = bitcount(octet >> 1)
    index += 1
    while (octet & 1):
        octet = struct.unpack('>B', data[index:index + 1])[0]
        subfields += bitcount(octet >> 1)
        index += 1
    return index + subfields

def dataItem070(index, data, smm):
    rep = struct.unpack('>B', data[index:index + 1])[0]
    return index + (rep * 2)

def dataItem080(index, data, smm):
    octet = struct.unpack('>B', data[index:index + 1])[0]
    subfields = bitcount(octet >> 1)
    index += 1
    while (octet & 1):
        octet = struct.unpack('>B', data[index:index + 1])[0]
        subfields += bitcount(octet >> 1)
        index += 1
    return index + subfields

def dataItem090(index, data, smm):
    return index + 2

def dataItem100(index, data, smm):
    return index + 8

def dataItem110(index, data, smm):
    return index + 1

def dataItem120(index, data, smm):
    return index + 8
#######################################


# returns a tuple containing:
# - the FSPEC integer value
# - the number of octets (length) of the FSPEC
def getFspec(data, start):
        length = 0
        octet = struct.unpack('>B', data[start])[0] 
        while(octet & 1):
            length = length + 1
            octet = (octet << 8) + struct.unpack('>B', data[start + length])[0]
        return octet, length + 1


# dump as hex string
def toHexString(data):
    return ':'.join(x.encode('hex') for x in data)

# count bits=1
def bitcount(number):
    count = 0
    while(number):
        number &= number - 1
        count += 1
    return count

# for dummies
def usage():
    print 'usage: astsectorcheck <asterix-file>'

# main
def main():
    # init
    global rotation_
    rotation_ = getNewRotationList()
    
    # DEBUG
    #sys.argv.append('data/wan-btcs.ast')
     
    # check command line arguments
    if len(sys.argv) < 2:
        usage()
        sys.exit(-1)

    astfile = sys.argv[1]
    parseAsterixFile(astfile)


if __name__ == '__main__':
    main()
