import sys
from PointingInterface_bib import *

if __name__ == '__main__':
    # names and colors of the points
    points=[
        ['Point 1', [255,255,0]],
        ['Point 2', [0,255,255]],
        ['Point 3', [255,0,255]],
        ]
    # path of the images
    path='.\\example\\*.jpg'
    
    interface=Interface(points, path)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()