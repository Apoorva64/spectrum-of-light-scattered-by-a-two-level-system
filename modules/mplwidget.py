# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvas

from matplotlib.figure import Figure
import matplotlib as mpl


class MplWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        color = '#232629'
        self.figure = Figure()

        self.canvas = FigureCanvas(self.figure)

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)

        self.setLayout(vertical_layout)

