# -*- mode: python -*-

import os

def addAll(folderPath,attrib = "Data", prefix = ""):
    res = []
    for fold, subs, files in os.walk(folderPath):
        for fName in files:
            res += [(prefix+fName,os.path.join(fold,fName),attrib)]

    return res


a = Analysis(['../spimagine/bin/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine'],
             hiddenimports=[
                 'scipy.special._ufuncs_cxx',
                 'scipy.linalg.cython_blas',
                 'scipy.linalg.cython_lapack',
<<<<<<< HEAD
                 "pyfft",
                 "pyopencl"],
=======
                 "pyfft"],
>>>>>>> 20ec0e4182d73c6cadf148a85b6d16af2fdeff32
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)



a.datas += addAll("../spimagine/volumerender/kernels")
a.datas += addAll("../spimagine/gui/images")
a.datas += addAll("../spimagine/colormaps")


a.datas += addAll("/Users/mweigert/python/gputools/gputools/convolve/kernels")
a.datas += addAll("/Users/mweigert/python/gputools/gputools/transforms/kernels")
a.datas += addAll("/Users/mweigert/python/pyopencl/build/lib.macosx-10.9-x86_64-2.7/pyopencl/cl")

<<<<<<< HEAD
a.datas += addAll("../spimagine/data/")

=======

# a.datas += [("lucy_richardson.cl","/Users/mweigert/python/Deconvolution/lucy_richardson.cl","Data")]


# include the libtiff dylib and all the py files (work around)
>>>>>>> 20ec0e4182d73c6cadf148a85b6d16af2fdeff32
a.datas += addAll("/Library/Python/2.7/site-packages/pyfft", prefix="pyfft/")

print a.datas

<<<<<<< HEAD
with open("_DATAS.txt","w") as f:
    f.write(str(a.datas))

with open("_BINARIES.txt","w") as f:
    f.write(str(a.binaries))

with open("_PURE.txt","w") as f:
    f.write(str(a.pure))

print a.binaries


# filter binaries.. exclude some dylibs that pyinstaller packaged but
# we actually dont need (e.g. wxPython)

import re
reg = re.compile(".*(sparsetools|QtWebKit|wxPython|matplotlib).*")

a.binaries = [s for s in a.binaries if reg.match(s[1]) is None] 


with open("_BINARIES_FILTER.txt","w") as f:
    f.write(str(a.binaries))
=======


# a.datas += [("tiff_h_4_0_3.py","/Library/Python/2.7/site-packages/libtiff/tiff_h_4_0_3.py","Data")]



# a.binaries += addAll("/usr/local/Cellar/libtiff/4.0.3/lib/","BINARY")


# a.binaries += [("libtiff.dylib","/usr/local/lib/libtiff.dylib","BINARY")]

# a.binaries += [("libtiff.dylib","/usr/local/Cellar/libtiff/4.0.3/lib/libtiff.dylib","BINARY")]

print a.binaries
>>>>>>> 20ec0e4182d73c6cadf148a85b6d16af2fdeff32


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine',
          # debug=False,
          debug=True,
          strip=None,
          upx=True,
          console=False )

app = BUNDLE(exe,
             name='spimagine.app',
             icon=None)


# b = Analysis(['../spimagine/spim_render.py'],
#              pathex=['/Users/mweigert/python/spimagine/spimagine'],
#              hiddenimports=[],
#              hookspath=None,
#              runtime_hooks=None)
# pyz = PYZ(b.pure)


# b.datas += addAll("../spimagine/kernels")

# b.datas += addAll("/Library/Python/2.7/site-packages/libtiff")

# b.binaries += [("libtiff.5.dylib","/usr/local/lib/libtiff.5.dylib","BINARY")]


# pyz = PYZ(b.pure)
# exe = EXE(pyz,
#           b.scripts,
#           b.binaries,
#           b.zipfiles,
#           b.datas,
#           name='spimagine_render',
#           debug=True,
#           strip=None,
#           upx=True,
#           console=True)
