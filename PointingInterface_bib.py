import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
from PIL import Image
import PIL.ExifTags
import os

from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.dockarea import DockArea, Dock

import glob

class Point():
    current_img = None
    def __init__(self, imgView, name='Point', color=[255,0,255]):
        self.name=name
        self.color=color
        self.sp = pg.ScatterPlotItem(size=15, pen=pg.mkPen(None), brush=pg.mkBrush(color), symbol='+')
        imgView.addItem(self.sp)
        try:
            self.data = np.load('{}.npy'.format(self.name),allow_pickle='TRUE').item()
        except:
            self.data={}
        self.update()

    def set_current_img(self, fname):
        self.__class__.current_img=fname

    def set_pos(self, pos):
        self.sp.setData([{'pos': pos}])
        if type(pos) is list:
            self.data[self.__class__.current_img]=[pos[0], pos[1]]
        else:
            self.data[self.__class__.current_img]=[pos.x(), pos.y()]

    def copy_previous(self):
        Limgs=list(self.data.keys())
        Limgs.append(self.__class__.current_img)
        Limgs.sort()
        i=Limgs.index(self.__class__.current_img)
        if i>0:
            x=self.data[Limgs[i-1]][0]
            y=self.data[Limgs[i-1]][1]
            self.set_pos([x,y])

    def del_pos(self):
        self.sp.setData([])
        try:
            del self.data[self.__class__.current_img]
        except:
            pass

    def update(self):
        if self.__class__.current_img in self.data:
            self.sp.setData([{'pos': self.data[self.__class__.current_img]}])
        else:
            self.sp.setData([])

    def save(self):
        np.save('{}.npy'.format(self.name), self.data) 

    def get_name(self):
        return self.name
    def get_color(self):
        return self.color


class KeyPressWindow(QtGui.QMainWindow):
    sigKeyPress = QtCore.pyqtSignal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def keyPressEvent(self, ev):
        self.sigKeyPress.emit(ev)

class MyImageView(pg.ImageView):
    sigMouseClicked = QtCore.pyqtSignal(object)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.scene.sigMouseClicked.connect(self.mouse_clicked)    
    def mouse_clicked(self, mouseClickEvent):
        self.sigMouseClicked.emit(mouseClickEvent)

class Interface():
    def __init__(self, points, path='.\\*.jpg'):
        """
        points: list defining the names and colors of the points, 
            example: points=[['Point 1', [255,255,0]], ['Point 2', [255,0,255]]]
        path: path of the images
        """
        self.app = QtGui.QApplication([])
        self.win = KeyPressWindow()
        self.win.sigKeyPress.connect(self.keyPressed)
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        self.win.resize(1600,900)
        self.win.setWindowTitle('Pointing Interface')
        self.w_img=MyImageView()
        
        self.path=path
        os.chdir(os.path.dirname(path))
        #Points
        self.Lpoints=[Point(self.w_img, pt[0], color=pt[1]) for pt in points]

        # Docks
        self.d_command = Dock("Commands", size=(200,80))
        self.d_img = Dock("Image", size=(800,900))
        self.d_table = Dock("Table", size=(200,900))

        self.area.addDock(self.d_command, 'top')
        self.area.addDock(self.d_table, 'bottom')
        self.area.addDock(self.d_img, 'right')

        params=[]
        for pt in self.Lpoints:
            params.append({'name': pt.get_name(), 'type': 'group', 'expanded':True, 'children': [
                    {'name': 'Select', 'type': 'action'},
                    {'name': 'Actif', 'type': 'bool', 'value': False, 'readonly': True},
                    {'name': 'Color', 'type': 'color', 'value':pt.get_color(), 'readonly': True},
                    {'name': 'Save', 'type': 'action'},
                ]})
        self.p = Parameter.create(name='params', type='group', children=params)
        for i in range(len(self.Lpoints)):
            self.p.param(self.Lpoints[int(i)].get_name(), 'Select').sigActivated.connect(lambda _,b=self.Lpoints[i]: self.ptSelect(b))
            self.p.param(self.Lpoints[int(i)].get_name(), 'Save').sigActivated.connect(lambda _,b=self.Lpoints[i]: self.ptSave(b))

        self.ptSelect(self.Lpoints[0])

        self.t = ParameterTree()
        self.t.setParameters(self.p, showTop=False)
        self.d_table.addWidget(self.t)
        
        self.w_img.sigMouseClicked.connect(self.mouseClick)
        self.w_img.setImage(np.random.normal(size=(100,100)))
        self.d_img.addWidget(self.w_img)

        self.save_label = QtGui.QLabel()
        self.w_command = pg.LayoutWidget()

        self.label_folder = QtGui.QLabel("")
        self.label_img = QtGui.QLabel("")
        self.spinbox_n=pg.SpinBox(value=0, bounds=[0, 1000], int=True, minStep=1, step=1, wrapping=True)
        goBtn = QtGui.QPushButton('Go')
        prevBtn = QtGui.QPushButton('Prev (<)')
        nextBtn = QtGui.QPushButton('Next (>)')
        instructions = QtGui.QLabel("Left click : Add or move point\nRight click : Menu\nd : Remove point\nc : Copy point from previous image")

        prevBtn.clicked.connect(lambda: self.change_img(False))
        nextBtn.clicked.connect(lambda: self.change_img(True))
        goBtn.clicked.connect(self.go)

        # restoreBtn.setEnabled(False)
        self.w_command.addWidget(self.label_img, row=0)
        self.w_command.addWidget(self.label_folder, row=1)
        self.w_command.addWidget(self.spinbox_n, row=2, col=0)
        self.w_command.addWidget(goBtn, row=2, col=1)
        self.w_command.addWidget(prevBtn, row=3, col=0)
        self.w_command.addWidget(nextBtn, row=3, col=1)
        self.w_command.addWidget(instructions, row=4, col=0)
        self.d_command.addWidget(self.w_command)

        self.win.show()

        self.init()

    def init(self):
        self.filesnames=[]
        self.current_index=0
        self.load_folder()
        self.load_img()

    def mouseClick(self, mouseClickEvent):
        if mouseClickEvent.button() == 1:
            self.current_point.set_pos(self.w_img.getImageItem().mapFromScene(mouseClickEvent.pos()))

    def keyPressed(self,evt):
        if evt.key() == 62: #key >
            self.change_img(next=True)
        elif evt.key() == 60: #key <
            self.change_img(next=False)
        elif evt.key() == 67:#key c
            self.current_point.copy_previous()
        elif evt.key() == 68:#key d
            self.current_point.del_pos()

    def ptSelect(self, ptref):
        for i in range(len(self.Lpoints)):
            self.p.param(self.Lpoints[int(i)].get_name(), 'Actif').setValue(False)
        self.current_point=ptref
        self.p.param(ptref.get_name(), 'Actif').setValue(True)

    def ptSave(self, ptref):
        ptref.save()

    def load_folder(self):
        self.filesnames=glob.glob(os.path.basename(self.path))
        if not self.filesnames:
            raise Exception('No images found.')
        self.spinbox_n.setRange(0, len(self.filesnames))

    def load_img(self):
        img=Image.open(self.filesnames[self.current_index])
        if img.mode=='RGB':
            axes={'x':1, 'y':0, 'c':2}
        else:
            axes={'x':1, 'y':0}
        self.w_img.setImage(np.array(img), axes=axes,autoRange=False)
        try:
            exif_data = img.getexif()
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img.getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            # 'DateTimeOriginal'
            date=exif_data[36867]
        except:
            date='No Exif data'
        self.label_img.setText('{}/{}\n File : {}\n Date : {}'.format(self.current_index, len(self.filesnames)-1, self.filesnames[self.current_index],date))
        self.current_point.set_current_img(self.filesnames[self.current_index])
        for pt in self.Lpoints:
            pt.update()

    def go(self):
        self.current_index=self.spinbox_n.value()
        self.load_img()

    def change_img(self, next=True):
        if next and self.current_index<len(self.filesnames)-1:
            self.current_index+=1
        elif self.current_index>0:
            self.current_index-=1
        self.load_img()
