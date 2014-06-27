#!/usr/bin/env python

"""
the (Qt) data models for usage in the gui frame

generic containers are defined for BScope Spim Data (SpimData)
and Tiff files (TiffData).
Extend it if you want to and change the DataLoadModel.chooseContainer to
accept it via dropg

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import logging
logger = logging.getLogger(__name__)

import os
import numpy as np
from PyQt4 import QtCore
import time
import re
from collections import defaultdict
import SpimUtils


############################################################################
"""
Te next classes define simple 4d Data Structures that implement the interface
given by GenericData
"""

class GenericData():
    """abstract base class for 4d data"""
    dataFileError = Exception("not a valid file")
    def __init__(self, name = ""):
        self.stackSize = None
        self.stackUnits = None
        self.name = name

    def sizeT(self):
        return self.stackSize[0]

    def size(self):
        return self.stackSize

    def __getitem__(self,int):
        return None


class SpimData(GenericData):
    """data class for spim data saved in folder fName
    fname/
    |-- metadata.txt
    |-- data/
       |--data.bin
       |--index.txt
    """
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self,fName):
        if fName:
            try:
                self.stackSize = SpimUtils.parseIndexFile(os.path.join(fName,"data/index.txt"))
                self.stackUnits = SpimUtils.parseMetaFile(os.path.join(fName,"metadata.txt"))
                self.fName = fName
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as SpimData"%fName)

            try:
                # try to figure out the dimension of the dark frame stack
                darkSizeZ = os.path.getsize(os.path.join(self.fName,"data/darkstack.bin"))/2/self.stackSize[2]/self.stackSize[3]
                with open(os.path.join(self.fName,"data/darkstack.bin"),"rb") as f:
                    self.darkStack = np.fromfile(f,dtype="<u2").reshape([darkSizeZ,self.stackSize[2],self.stackSize[3]])

            except Exception as e:
                logger.warning("couldn't find darkstack (%s)",e)


    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            if pos<0 or pos>=self.stackSize[0]:
                raise IndexError("0 <= pos <= %i, but pos = %i"%(self.stackSize[0]-1,pos))


            pos = max(0,min(pos,self.stackSize[0]-1))
            voxels = np.prod(self.stackSize[1:])
            # use int64 for bigger files
            offset = np.int64(2)*pos*voxels

            with open(os.path.join(self.fName,"data/data.bin"),"rb") as f:
                f.seek(offset)
                return np.fromfile(f,dtype="<u2",
                count=voxels).reshape(self.stackSize[1:])
        else:
            return None


class TiffData(GenericData):
    """3d tiff data"""
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self,fName, stackUnits = [1.,1.,1.]):
        if fName:
            try:
                self.stackSize = (1,)+ SpimUtils.getTiffSize(fName)
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as TiffData"%fName)
                return

            self.stackUnits = stackUnits
            self.fName = fName


    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            return SpimUtils.read3dTiff(self.fName)
        else:
            return None


class NumpyData(GenericData):

    def __init__(self, data, stackUnits = [1.,1.,1.]):
        GenericData.__init__(self,"NumpyData")

        if len(data.shape)==3:
            self.stackSize = (1,) + data.shape
            self.data = data.copy().reshape(self.stackSize)
        elif len(data.shape)==4:
            self.stackSize = data.shape
            self.data = data.copy()
        else:
            raise TypeError("data should be 3 or 4 dimensional! shape = %s" %str(data.shape))


        self.stackUnits = stackUnits

    def __getitem__(self,pos):
        return self.data[pos,...]


class DemoData(GenericData):
    def __init__(self, N = 100):
        GenericData.__init__(self,"DemoData")
        self.load(N)

    def load(self,N = 100):
        self.stackSize = (1,N,N,N/2)
        self.fName = ""
        self.nT = N
        self.stackUnits = (1,1,1)
        x = np.linspace(-1,1,N)
        Z,Y,X = np.meshgrid(x,x,x , indexing = "ij")
        R = np.sqrt(X**2+Y**2+Z**2)
        R2 = np.sqrt((X-.4)**2+(Y+.2)**2+Z**2)
        phi = np.arctan2(Z,Y)
        theta = np.arctan2(X,np.sqrt(Y**2+Z**2))
        u = np.exp(-500*(R-1.)**2)*np.sum(np.exp(-150*(-theta-t+.1*(t-np.pi/2.)*
            np.exp(-np.sin(2*(phi+np.pi/2.))))**2)
            for t in np.linspace(-np.pi/2.,np.pi/2.,10))*(1+Z)

        u2 = np.exp(-7*R2**2)
        self.data = (10000*(u + 2*u2)).astype(np.int16)


    def sizeT(self):
        return self.nT

    def __getitem__(self,pos):
        return self.data


class EmptyData(GenericData):
    def __init__(self):
        GenericData.__init__(self,"EmptyData")
        self.stackSize = (1,1,1,1)
        self.fName = ""
        self.nT = 1
        self.stackUnits = (1,1,1)
        self.data = np.zeros((1,1,1)).astype(np.uint16)

    def sizeT(self):
        return self.nT

    def __getitem__(self,pos):
        return self.data

    

############################################################################
"""
this defines the qt enabled data models based on the GenericData structure

each dataModel starts a prefetching thread, that loads next timepoints in
the background
"""


class DataLoadThread(QtCore.QThread):
    """the prefetching thread for each data model"""
    def __init__(self, _rwLock, nset = set(), data = None,dataContainer = None):
        QtCore.QThread.__init__(self)
        self._rwLock = _rwLock
        if nset and data and dataContainer:
            self.load(nset, data, dataContainer)


    def load(self, nset, data, dataContainer):
        self.nset = nset
        self.data = data
        self.dataContainer = dataContainer


    def run(self):
        self.stopped = False
        while not self.stopped:
            kset = set(self.data.keys())
            dkset = kset.difference(set(self.nset))
            dnset = set(self.nset).difference(kset)

            for k in dkset:
                del(self.data[k])

            if dnset:
                logger.debug("preloading %s", list(dnset))
                for k in dnset:
                    newdata = self.dataContainer[k]
                    self._rwLock.lockForWrite()
                    self.data[k] = newdata
                    self._rwLock.unlock()
                    logger.debug("preload: %s",k)
                    time.sleep(.0001)

            time.sleep(.0001)


class DataModel(QtCore.QObject):
    """the data model
    emits signals when source/time position has changed
    """
    _dataSourceChanged = QtCore.pyqtSignal()
    _dataPosChanged = QtCore.pyqtSignal(int)

    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, dataContainer = None, prefetchSize = 0):
        super(DataModel,self).__init__()
        self.dataLoadThread = DataLoadThread(self._rwLock)
        self._dataSourceChanged.connect(self.dataSourceChanged)
        self._dataPosChanged.connect(self.dataPosChanged)
        if dataContainer:
            self.setContainer(dataContainer, prefetchSize)

    @classmethod
    def fromPath(self,fName, prefetchSize = 0):
        d = DataModel()
        d.loadFromPath(fName,prefetchSize)
        return d

    def setContainer(self,dataContainer = None, prefetchSize = 0):
        self.dataContainer = dataContainer
        self.prefetchSize = prefetchSize
        self.nset = []
        self.data = defaultdict(lambda: None)

        if self.dataContainer:
            if prefetchSize > 0:
                self.stopDataLoadThread()
                self.dataLoadThread.load(self.nset,self.data, self.dataContainer)
                self.dataLoadThread.start(priority=QtCore.QThread.LowPriority)
            self._dataSourceChanged.emit()
            self.setPos(0)

    def getName(self):
        return self.dataContainer.name

    def __repr__(self):
        return "DataModel: %s \t %s"%(self.dataContainer.name,self.size())

    def dataSourceChanged(self):
        logger.info("data source changed:\n%s",self)

    def dataPosChanged(self, pos):
        logger.info("data position changed to %i",pos)



    def stopDataLoadThread(self):
        self.dataLoadThread.stopped = True

    def prefetch(self,pos):
        self._rwLock.lockForWrite()
        self.nset[:] = self.neighborhood(pos)
        self._rwLock.unlock()

    def sizeT(self):
        if self.dataContainer:
            return self.dataContainer.sizeT()

    def size(self):
        if self.dataContainer:
            return self.dataContainer.size()

    def name(self):
        if self.dataContainer:
            return self.dataContainer.name

    def stackUnits(self):
        if self.dataContainer:
            return self.dataContainer.stackUnits

    def setPos(self,pos):
        if pos<0 or pos>=self.sizeT():
            raise IndexError("setPos(pos): %i outside of [0,%i]!"%(pos,self.sizeT()-1))
            return

        self.pos = pos
        self._dataPosChanged.emit(pos)
        self.prefetch(self.pos)


    def __getitem__(self,pos):
        # self._rwLock.lockForRead()
        if not hasattr(self,"data"):
            return None

        if not self.data.has_key(pos):
            newdata = self.dataContainer[pos]
            self._rwLock.lockForWrite()
            self.data[pos] = newdata
            self._rwLock.unlock()



        if self.prefetchSize > 0:
            self.prefetch(pos)

        return self.data[pos]



    def neighborhood(self,pos):
        # FIXME mod stackSize!
        return np.arange(pos,pos+self.prefetchSize+1)%self.sizeT()

    def loadFromPath(self,fName, prefetchSize = 0):
        if re.match(".*\.tif",fName):
            self.setContainer(TiffData(fName),prefetchSize)
        else:
            self.setContainer(SpimData(fName),prefetchSize)




def test_spimdata():
    d = SpimData("/Users/mweigert/Data/HisGFP")

    m = DataModel(d)

    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])


def test_tiffdata():
    d = TiffData("/Users/mweigert/Data/droso_test.tif")

    m = DataModel(d)

    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])


def test_numpydata():
    d = NumpyData(np.ones((10,100,100,100)))


    m = DataModel(d)

    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])

def test_frompath():
    m = DataModel.fromPath("/Users/mweigert/Data/HisGFP")
    m = DataModel.fromPath("/Users/mweigert/Data/droso_test.tif")


if __name__ == '__main__':

    # test_spimdata()

    # test_tiffdata()
    # test_numpydata()

    # test_frompath()

    N = 256

    d = NumpyData(np.ones((N,N,N)))