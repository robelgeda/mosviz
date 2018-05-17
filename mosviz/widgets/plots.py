from __future__ import absolute_import, division, print_function

from qtpy import QtCore
from qtpy import PYQT5

from glue.icons.qt import get_icon
from glue.viewers.common.qt.tool import CheckableTool, Tool
from glue.viewers.common.qt.mouse_mode import MouseMode
from glue.viewers.common.qt.toolbar import BasicToolbar
from qtpy import PYQT5
from qtpy.QtWidgets import QMainWindow
from qtpy.QtCore import Signal

import matplotlib.pyplot as plt
if PYQT5:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle

try:
    from glue.viewers.image.qt.standalone_image_viewer import StandaloneImageViewer
except ImportError:
    from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget as StandaloneImageViewer

from glue.viewers.common.viz_client import init_mpl



__all__ = ['Line1DWidget', 'DrawableImageWidget', 'MOSImageWidget']

class MatplotlibViewerToolbar(BasicToolbar):

    pan_begin = QtCore.Signal()
    pan_end = QtCore.Signal()

    def __init__(self, viewer):

        self.canvas = viewer.central_widget.canvas

        # Set up virtual Matplotlib navigation toolbar (don't show it)
        self._mpl_nav = NavigationToolbar2QT(self.canvas, viewer)
        self._mpl_nav.hide()

        BasicToolbar.__init__(self, viewer)

        viewer.window_closed.connect(self.close)

    def close(self, *args):
        self._mpl_nav.setParent(None)
        self._mpl_nav.parent = None

    def setup_default_modes(self):

        # Set up default Matplotlib Tools - this gets called by the __init__
        # call to the parent class above.

        home_mode = HomeTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(home_mode)

        save_mode = SaveTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(save_mode)

        back_mode = BackTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(back_mode)

        forward_mode = ForwardTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(forward_mode)

        pan_mode = PanTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(pan_mode)

        zoom_mode = ZoomTool(self.parent(), toolbar=self._mpl_nav)
        self.add_tool(zoom_mode)

        self._connections = []

    def activate_tool(self, mode):
        if isinstance(mode, MouseMode):
            self._connections.append(self.canvas.mpl_connect('button_press_event', mode.press))
            self._connections.append(self.canvas.mpl_connect('motion_notify_event', mode.move))
            self._connections.append(self.canvas.mpl_connect('button_release_event', mode.release))
            self._connections.append(self.canvas.mpl_connect('key_press_event', mode.key))
        super(MatplotlibViewerToolbar, self).activate_tool(mode)

    def deactivate_tool(self, mode):
        for connection in self._connections:
            self.canvas.mpl_disconnect(connection)
        self._connections = []
        super(MatplotlibViewerToolbar, self).deactivate_tool(mode)

class Line1DWidget(QMainWindow):
    window_closed = Signal()

    def __init__(self, parent=None):
        super(Line1DWidget, self).__init__(parent)

        self.figure = plt.figure(facecolor='white')

        # Canvas Widget that displays the `figure` it takes the `figure`
        # instance as a parameter to __init__
        canvas = FigureCanvas(self.figure)

        # Double reference; Glue's toolbar abstraction requires that the
        # central widget of its parent have a reference to the canvas object
        self.central_widget = canvas
        self.central_widget.canvas = canvas

        # Navigation widget, it takes the Canvas widget and a parent
        self.toolbar = MatplotlibViewerToolbar(self)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.central_widget)

        _, self._axes = init_mpl(figure=self.figure)
        self._artists = []

    @property
    def axes(self):
        return self._axes

    def set_data(self, x, y, yerr=None):

        # Note: we can't use self._axes.cla() here since that removes events
        # which will cause the locked axes to not work.
        for artist in self._artists:
            try:
                artist.remove()
            except ValueError:  # some artists may already not be in plot
                pass

        # Plot data
        if yerr is None:
            self._artists = self._axes.plot(x, y, color='k')
        else:
            self._artists = [self._axes.errorbar(x, y, yerr=yerr, color='k')]

        # Refresh canvas
        self._redraw()

    def _redraw(self):
        self.central_widget.canvas.draw()

    def set_status(self, message):
        pass


class MOSImageWidget(StandaloneImageViewer):

    def __init__(self, *args, **kwargs):
        super(MOSImageWidget, self).__init__(*args, **kwargs)

    def set_status(self, status):
        pass


class DrawableImageWidget(MOSImageWidget):

    def __init__(self, *args, **kwargs):
        super(DrawableImageWidget, self).__init__(*args, **kwargs)
        self._slit_patch = None

    def draw_rectangle(self, x=None, y=None, width=None, height=None):
        if self._slit_patch is not None:
            self._slit_patch.remove()
        self._slit_patch = Rectangle((x - width / 2, y - height / 2),
                                     width=width, height=height,
                                     edgecolor='red', facecolor='none')
        self._axes.add_patch(self._slit_patch)
