import typing as t

from PySide2 import QtCore, QtWidgets, QtGui

from static.stylesheets import BUTTON_SET_STYLESHEET

class ButtonSet(QtWidgets.QWidget):
    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, parent)

        self._button_set_layout = QtWidgets.QHBoxLayout(self)

        self.next_button = QtWidgets.QPushButton('Next (D) -->', self)
        self.prev_button = QtWidgets.QPushButton('<-- Prev (A)', self)
        self.rerun_button = QtWidgets.QPushButton('Rerun (R)', self)
        self.run_button = QtWidgets.QPushButton('Run (S)', self)
        self.stop_button = QtWidgets.QPushButton('Stop (S)', self)
        # TODO: add clear button, run backwards button
        self.setStyleSheet(BUTTON_SET_STYLESHEET)
        
        self.stop_button.setEnabled(False)

        self.prev_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_A))
        self.next_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_D))
        self.rerun_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_R))
        # one button should always be disabled --> no conflict
        self.run_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_S))
        self.stop_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_S))

        self._button_set_layout.addWidget(self.prev_button, alignment=QtCore.Qt.AlignLeft)
        self._button_set_layout.addWidget(self.stop_button, alignment=QtCore.Qt.AlignCenter)
        self._button_set_layout.addWidget(self.rerun_button, alignment=QtCore.Qt.AlignCenter)
        self._button_set_layout.addWidget(self.run_button, alignment=QtCore.Qt.AlignCenter)
        self._button_set_layout.addWidget(self.next_button, alignment=QtCore.Qt.AlignRight)

        self.setLayout(self._button_set_layout)
