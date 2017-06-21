import pyqtgraph as pg
import numpy as np
from pyqtgraph import GraphicsLayoutWidget
from pyqtgraph.Qt import QtGui, QtCore



class monitorMainWidget(QtGui.QWidget):
    """Widget for holding the images generated by the camera.
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        # General layout of the widget to hold an image and a histogram
        self.layout = QtGui.QHBoxLayout(self)

        # Settings for the image
        self.viewport = GraphicsLayoutWidget()
        self.view = self.viewport.addViewBox(lockAspect = False, enableMenu=True)

        self.autoScale = QtGui.QAction("Auto Range", self.view.menu)
        self.autoScale.triggered.connect(self.doAutoScale)
        self.view.menu.addAction(self.autoScale)

        self.img = pg.ImageItem()
        self.view.addItem(self.img)
        self.imv = pg.ImageView(view=self.view, imageItem=self.img)

        # Add everything to the widget
        self.layout.addWidget(self.imv)
        self.setLayout(self.layout)

        self.showCrosshair = False
        self.showCrossCut = False

    def setup_overlay(self):
        # useful if one want to plot the recovered trajectory in the camera viewport
        self.img2 = pg.ImageItem() # To overlay another image if needed.
        self.img2.setOpacity(0.4)
        self.img2.setZValue(1000)
        self.view.addItem(self.img2)

    def setup_cross_hair(self, max_size):
        """Sets up a cross hair."""
        self.crosshair = []
        self.crosshair.append(pg.InfiniteLine(angle=0, movable=False, pen={'color': 124, 'width': 4}))
        self.crosshair.append(pg.InfiniteLine(angle=90, movable=False, pen={'color': 124, 'width': 4}))
        self.crosshair[0].setBounds((1, max_size[1] - 1))
        self.crosshair[1].setBounds((1, max_size[0] - 1))

    def setup_cross_cut(self, max_size):
        """Set ups the horizontal line for the cross cut."""
        self.crossCut = pg.InfiniteLine(angle=0, movable=False, pen={'color': 'g', 'width': 2})
        self.crossCut.setBounds((1, max_size))

    def setup_roi_lines(self, max_size):
        """Sets up the ROI lines surrounding the image.
        
        :param list max_size: List containing the maximum size of the image to avoid ROIs bigger than the CCD."""

        self.hline1 = pg.InfiniteLine(angle=0, movable=True, hoverPen={'color': "FF0", 'width': 4})
        self.hline2 = pg.InfiniteLine(angle=0, movable=True, hoverPen={'color': "FF0", 'width': 4})
        self.vline1 = pg.InfiniteLine(angle=90, movable=True, hoverPen={'color': "FF0", 'width': 4})
        self.vline2 = pg.InfiniteLine(angle=90, movable=True, hoverPen={'color': "FF0", 'width': 4})

        self.vline2.setValue(max_size[0] - 1)
        self.hline2.setValue(max_size[1] - 1)
        self.hline1.setBounds((1, max_size[1] - 1))
        self.hline2.setBounds((1, max_size[1] - 1))
        self.vline1.setBounds((1, max_size[0] - 1))
        self.vline2.setBounds((1, max_size[0] - 1))
        self.view.addItem(self.hline1)
        self.view.addItem(self.hline2)
        self.view.addItem(self.vline1)
        self.view.addItem(self.vline2)

    def setup_mouse_tracking(self):
        self.imv.setMouseTracking(True)
        self.imv.getImageItem().scene().sigMouseMoved.connect(self.mouseMoved)
        self.imv.getImageItem().scene().contextMenu = None

    def keyPressEvent(self,key):
        """Triggered when there is a key press with some modifier.
        Shift+C: Removes the cross hair from the screen
        Ctrl+C: Emits a specialTask signal
        Ctrl+V: Emits a stopSpecialTask signal
        These last two events have to be handeled in the mainWindow that implemented this widget."""
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            if key.key() == 67: # For letter C of 'Clear
                if self.showCrosshair:
                    for c in self.crosshair:
                        self.view.removeItem(c)
                    self.showCrosshair = False
                if self.showCrossCut:
                    self.view.removeItem(self.crossCut)
                    self.showCrossCut = False
        elif modifiers == QtCore.Qt.ControlModifier:
            if key.key() == 67: # For letter C of 'Clear
                self.emit(QtCore.SIGNAL('specialTask'))
            if key.key() == 86: # For letter V
                self.emit(QtCore.SIGNAL('stopSpecialTask'))

    def mouseMoved(self,arg):
        """Updates the position of the cross hair. The mouse has to be moved while pressing down the Ctrl button."""
        # arg = evt.pos()
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            if not self.showCrosshair:
                for c in self.crosshair:
                    self.view.addItem(c)
                self.showCrosshair = True
            self.crosshair[1].setValue(int(self.img.mapFromScene(arg).x()))
            self.crosshair[0].setValue(int(self.img.mapFromScene(arg).y()))
        elif modifiers == QtCore.Qt.AltModifier:
            if not self.showCrossCut:
                self.view.addItem(self.crossCut)
            self.showCrossCut = True
            self.crossCut.setValue(int(self.img.mapFromScene(arg).y()))

    def doAutoScale(self):
        h, y = self.img.getHistogram()
        self.imv.setLevels(min(h),max(h))
        # self.img.HistogramLUTItem.setLevels(min(h),max(h))

    def drawTargetPointer(self, image, location):
        """gets an image and draws a square around the target location"""
        w = 5
        x0 = np.int(location[0])
        y0 = np.int(location[1])
        newimage = image/2
        for x in range(w):
            newimage[x0 + x, y0 - w + x, 1] = 3000
            newimage[x0 - x, y0 - w + x, 2] = 6000
            newimage[x0 + x, y0 + w - x, 2] = 6000
            newimage[x0 - x, y0 + w - x, 1] = 3000

        return newimage

    # def updateImage(self,img):
    #     """Updates the image being displayed.
    #     img -- numpy 2D array"""
    #     self.img.setImage(img)
    #     self.hist.setI