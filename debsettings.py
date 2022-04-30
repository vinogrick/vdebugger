from PySide2 import QtCore, QtWidgets, QtGui
import typing as t

from util import DebuggerSettings


class SettingsHandler:
    pass


class SettingsEditor(QtWidgets.QWidget):
    def __init__(self, settings_handler: SettingsHandler, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, None)  # None to open in a new window
        self.setWindowTitle('Debugger settings')

        self._settings_handler = settings_handler
        self._parent = parent

        self._main_layout = QtWidgets.QVBoxLayout(self)
        
        self._slider_box = QtWidgets.QGroupBox(self)
        self._slider_layout = QtWidgets.QVBoxLayout(self._slider_box)
        # TODO: add typing value in
        self._nsd_slider_lbl = QtWidgets.QLabel(f'Next step delay: {settings_handler.debugger_settings.next_step_delay}', self)
        self._next_step_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._next_step_delay_slider.setMinimum(10)
        self._next_step_delay_slider.setMaximum(2000)
        self._next_step_delay_slider.setValue(settings_handler.debugger_settings.next_step_delay)
        self._slider_layout.addWidget(self._nsd_slider_lbl, alignment=QtCore.Qt.AlignCenter)
        self._slider_layout.addWidget(self._next_step_delay_slider, alignment=QtCore.Qt.AlignVCenter)
        self._next_step_delay_slider.valueChanged.connect(self.slider_val_changed)

        self._btn_layout = QtWidgets.QHBoxLayout()
        self._save_btn = QtWidgets.QPushButton('Save', self)
        self._close_btn = QtWidgets.QPushButton('Close', self)
        self._btn_layout.addWidget(self._close_btn)
        self._btn_layout.addWidget(self._save_btn)

        self._save_btn.clicked.connect(self.save)
        self._close_btn.clicked.connect(self.close)

        self._main_layout.addWidget(self._slider_box)
        self._main_layout.addLayout(self._btn_layout)
        self.setLayout(self._main_layout)
    
    def slider_val_changed(self, value: int):
        real_value = value - value % 10  # round value
        self._next_step_delay_slider.setValue(real_value)
        self._nsd_slider_lbl.setText(f'Next step delay: {real_value}')

    def save(self):
        self._settings_handler.debugger_settings.next_step_delay = self._next_step_delay_slider.value()
        self.hide()
    
    def edit(self):
        self.show()
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._next_step_delay_slider.setValue(self._settings_handler.debugger_settings.next_step_delay)
        return super().closeEvent(event)


class SettingsHandler:
    def __init__(self, settings: DebuggerSettings, qt_parent: QtWidgets.QWidget) -> None:
        self.debugger_settings = settings
        self._settings_editor = SettingsEditor(self, qt_parent)
        self._settings_editor.hide()
    
    def edit_settings(self):
        self._settings_editor.edit()
    
    def set_settings(self, settings: DebuggerSettings):
        pass
