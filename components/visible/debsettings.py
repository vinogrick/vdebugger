from PySide2 import QtCore, QtWidgets, QtGui
import typing as t
import json

from components.static.const import SETTINGS_PATH, MIN_STEP_DELAY_MS, MAX_STEP_DELAY_MS
from components.static.stylesheets import SETTINGS_EDITOR_STYLESHEET

from components.internal.util import DebuggerSettings

class SettingsEditor(QtWidgets.QWidget):
    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, None)  # None to open in a new window
        self.setWindowTitle('Debugger settings')

        with open(SETTINGS_PATH, 'rt') as settings_file:
            self._settings = DebuggerSettings.deserialize(json.load(settings_file))
        self._parent = parent

        self._main_layout = QtWidgets.QVBoxLayout(self)
        
        self._slider_box = QtWidgets.QGroupBox(self)
        self._slider_layout = QtWidgets.QVBoxLayout(self._slider_box)
        # TODO: add typing value in
        self._nsd_slider_lbl = QtWidgets.QLabel(f'Next step delay: {self._settings.next_step_delay}', self)
        self._next_step_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._next_step_delay_slider.setMinimum(MIN_STEP_DELAY_MS)
        self._next_step_delay_slider.setMaximum(MAX_STEP_DELAY_MS)
        self._next_step_delay_slider.setValue(self._settings.next_step_delay)
        self._slider_layout.addWidget(self._nsd_slider_lbl, alignment=QtCore.Qt.AlignCenter)
        self._slider_layout.addWidget(self._next_step_delay_slider, alignment=QtCore.Qt.AlignVCenter)
        self._next_step_delay_slider.valueChanged.connect(self.slider_val_changed)

        self._btn_layout = QtWidgets.QHBoxLayout()
        self._save_btn = QtWidgets.QPushButton('Save', self)
        self._close_btn = QtWidgets.QPushButton('Close', self)
        self._reset_btn = QtWidgets.QPushButton('Reset', self)
        self._btn_layout.addWidget(self._close_btn)
        self._btn_layout.addWidget(self._reset_btn)
        self._btn_layout.addWidget(self._save_btn)

        self._save_btn.clicked.connect(self.save)
        self._close_btn.clicked.connect(self.close)
        self._reset_btn.clicked.connect(self.reset_settings)

        self._main_layout.addWidget(self._slider_box)
        self._main_layout.addLayout(self._btn_layout)
        self.setLayout(self._main_layout)

        self.setStyleSheet(SETTINGS_EDITOR_STYLESHEET)
    
    def slider_val_changed(self, value: int):
        real_value = value - value % 10  # round value
        self._next_step_delay_slider.setValue(real_value)
        self._nsd_slider_lbl.setText(f'Next step delay: {real_value}')

    def save(self):
        self._settings.next_step_delay = self._next_step_delay_slider.value()
        with open(SETTINGS_PATH, 'wt') as settings_file:
            json.dump(self._settings.serialize(), settings_file, indent=2)
        self.hide()
    
    def edit(self):
        self.show()
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._next_step_delay_slider.setValue(self._settings.next_step_delay)
        return super().closeEvent(event)
    
    def get_settings(self):
        return self._settings
    
    def reset_settings(self):
        self._settings = DebuggerSettings()
        with open(SETTINGS_PATH, 'wt') as settings_file:
            json.dump(self._settings.as_dict(), settings_file, indent=2)
        self._next_step_delay_slider.setValue(self._settings.next_step_delay)
