import typing as t

from PySide2 import QtCore, QtWidgets, QtGui

from components.static.stylesheets import BUTTON_SET_STYLESHEET

LAYOUT_GRID = {
    'W': (0, 1, 1, 1),
    'R': (0, 3, 1, 1),
    'A': (1, 0, 1, 1),
    'S': (1, 1, 1, 1),
    'D': (1, 2, 1, 1),
    'C': (2, 2, 1, 1),
}

class ButtonSet(QtWidgets.QWidget):
    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, parent)

        self._button_set_layout = QtWidgets.QGridLayout(self)

        self.next_button = QtWidgets.QPushButton('(D)\nNext -->', self)
        self.prev_button = QtWidgets.QPushButton('(A)\n<-- Prev', self)
        self.rerun_button = QtWidgets.QPushButton('(R)\nRerun', self)
        self.run_or_stop_button = QtWidgets.QPushButton('(S)\nRun/Stop', self)
        self.clear_button = QtWidgets.QPushButton('(C)\nClear', self)
        self.run_back_button = QtWidgets.QPushButton('(W)\nRun back', self)
        self.setStyleSheet(BUTTON_SET_STYLESHEET)

        self.prev_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_A))
        self.next_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_D))
        self.rerun_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_R))
        self.clear_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_C))
        self.run_back_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_W))
        self.run_or_stop_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_S))

        self._button_set_layout.addWidget(self.run_back_button, *LAYOUT_GRID['W'])
        self._button_set_layout.addWidget(self.prev_button, *LAYOUT_GRID['A'])
        self._button_set_layout.addWidget(self.rerun_button, *LAYOUT_GRID['R'])
        self._button_set_layout.addWidget(self.run_or_stop_button, *LAYOUT_GRID['S'])
        self._button_set_layout.addWidget(self.next_button, *LAYOUT_GRID['D'])
        self._button_set_layout.addWidget(self.clear_button, *LAYOUT_GRID['C'])

        # self._button_set_layout.addWidget(self.run_back_button, alignment=QtCore.Qt.AlignLeft)
        # self._button_set_layout.addWidget(self.prev_button, alignment=QtCore.Qt.AlignLeft)
        # self._button_set_layout.addWidget(self.rerun_button, alignment=QtCore.Qt.AlignCenter)
        # self._button_set_layout.addWidget(self.run_or_stop_button, alignment=QtCore.Qt.AlignCenter)
        # self._button_set_layout.addWidget(self.next_button, alignment=QtCore.Qt.AlignRight)
        # self._button_set_layout.addWidget(self.clear_button, alignment=QtCore.Qt.AlignRight)

        self.setLayout(self._button_set_layout)
