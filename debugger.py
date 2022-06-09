import argparse
import os.path as path
import typing as t

from PySide2 import QtCore, QtWidgets, QtGui

from components.visible.button_set import ButtonSet
from components.visible.debsettings import SettingsEditor
from components.visible.messagebox import MessageBox
from components.visible.nodedisplay import CentralDisplay
from components.visible.right_menu import EventMenu
from components.visible.startuppage import StartupPage

from components.internal.internal_logger import getLogger
from components.internal.logparser import LogParser
from components.internal.util import Test, SessionData, TestDebugData, FramedGroup

from components.static.stylesheets import MENU_BAR_STYLESHEET

# TODO:
# add run backwards

logger = getLogger('debugger')

class VDebugger:  # remove class?
    def __init__(self) -> None:
        self._session_data: SessionData = None

    def main(self, logfile_path: str):
        parser = LogParser()
        parser.parse_log_file(logfile_path)
        self._session_data = SessionData(parser.tests)
        self.start_gui()
    
    ############ GUI ############
    def start_gui(self):
        app = QtWidgets.QApplication([])
        main_window = MainWindow(self._session_data)
        screen_size = app.primaryScreen().size()
        main_window.resize(screen_size.width() // 2, screen_size.height() // 2)
        main_window.showMaximized()
        
        # main_window.setFixedSize(main_window.size())  # makes window nonresizable
        # main_window.show()
        logger.info(f'Debugger exited with status: {app.exec_()}')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, session_data: SessionData) -> None:
        QtWidgets.QMainWindow.__init__(self)
        self._session_data = session_data
        self._curr_test_debug_data: t.Optional[TestDebugData] = None

        self._menu_bar = self.menuBar()
        self._menu_bar.setStyleSheet(MENU_BAR_STYLESHEET)
        self._menu_bar.addAction('Main', self.show_main_page).setShortcut("Ctrl+M")

        self._tests_menus: t.Dict[str, QtWidgets.QMenu] = {
            'main': self._menu_bar.addMenu("Tests"),
            Test.Status.PASSED: None,
            Test.Status.FAILED: None
        }
        self._show_test_error_act = self._menu_bar.addAction('Show test error', self.show_test_error)
        self._show_test_error_act.setShortcut("Ctrl+E")
        self._show_test_error_act.setVisible(False)

        # add submenus by status
        for status in [Test.Status.PASSED, Test.Status.FAILED]:
            self._tests_menus[status] = self._tests_menus['main'].addMenu(status)
        
        # set actions
        self._tests_menu_callbacks = []
        for test in self._session_data.tests.values():
            self._tests_menu_callbacks.append(self.on_select_test_wrapper(test.name))
            self._tests_menus[test.status].addAction(
                test.name, self._tests_menu_callbacks[-1]
            )

        # central widget
        self._central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self._central_widget)

        self._central_layout = QtWidgets.QStackedLayout(self._central_widget)

        self._startup_page = StartupPage(self._session_data, self._tests_menu_callbacks, self)
        self._central_layout.addWidget(self._startup_page)

        # main widget in central layout
        self._horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        # splits node display and button_set with msg box
        self._vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)

        # settings handler
        self._settings_editor = SettingsEditor(self)
        self._menu_bar.addAction('Settings', self.set_settings)

        self._message_box = MessageBox(self)
        self._display = CentralDisplay(self)
        self._event_menu = EventMenu(self._display, self._settings_editor, self)
        self._button_set = ButtonSet(self)

        self._left_frame = FramedGroup(
            {
                'splitter': self._vertical_splitter
            },
            QtWidgets.QHBoxLayout,
            self
        )

        # nodes display
        self._display_frame = FramedGroup(
            {
                'display': self._display
            },
            QtWidgets.QHBoxLayout,
            self
        )

        # lower buttons set
        self._btn_and_msg_frame = FramedGroup(
            {
                'button_set': self._button_set,
                'vline': QtWidgets.QFrame(self, frameShape=QtWidgets.QFrame.VLine),
                'message_box': self._message_box
            }, 
            QtWidgets.QHBoxLayout,
            self
        )
        
        # events
        self._right_frame = FramedGroup(
            {
                'event_menu': self._event_menu
            }, 
            QtWidgets.QHBoxLayout,
            self
        )
        self._left_frame.setStyleSheet('margin: 0px')
        self._right_frame.setStyleSheet('margin: 0px')

        # connect buttons
        self._button_set.next_button.clicked.connect(self.next_step)
        self._button_set.prev_button.clicked.connect(self.prev_step)
        self._button_set.rerun_button.clicked.connect(self.rerun)
        self._button_set.clear_button.clicked.connect(self.clear)
        self._button_set.run_back_button.clicked.connect(self.run_backwards)
        self._button_set.run_or_stop_button.clicked.connect(self.run_or_stop)
        
        # timer for running
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.next_step)

        # timer for backwards running
        self._back_timer = QtCore.QTimer()
        self._back_timer.timeout.connect(self.prev_step)

        # specific event index to run to
        self._run_to_event_idx: t.Optional[int] = None

        # add splitters to main layout
        self._vertical_splitter.addWidget(self._display_frame)
        self._vertical_splitter.addWidget(self._btn_and_msg_frame)
        self._vertical_splitter.setSizes([60000, 10000])  # hack to set ratio, TODO: add to debsettings

        self._horizontal_splitter.addWidget(self._left_frame)
        self._horizontal_splitter.addWidget(self._right_frame)
        self._horizontal_splitter.setSizes([60000, 40000])  # hack to set ratio
        self._central_layout.addWidget(self._horizontal_splitter)
        
        self._menu_bar.addAction('Quit', self.close).setShortcut("Ctrl+W")
        
        self._central_widget.setLayout(self._central_layout)
        self._central_widget.showMaximized()
        self.on_startup()

    def on_startup(self):
        self.setWindowTitle("VDebugger")
    
    def on_select_test_wrapper(self, test_name: str):
        def on_select_test():
            logger.info(f'Selected test: {test_name}')
            test = self._session_data.tests[test_name]
            self.show_test_page()
            if self._curr_test_debug_data and self._curr_test_debug_data.test.name == test_name:
                # to start from where we were
                return
            
            self._curr_test_debug_data = TestDebugData(test)
            self.setWindowTitle(f"VDebugger | TEST: {test.name} | {test.status}")

            if test.err is not None:
                self._show_test_error_act.setVisible(True)
                self.show_test_error()
            else:
                self._show_test_error_act.setVisible(False)
                self._message_box.info(f'Selected test: {test_name}')

            self._event_menu.clear_events()

            self._display.set_node_ids(test.node_ids)
            self._display.on_startup()
        return on_select_test
    
    def clear(self):
        self._message_box.info(f'Clear events')
        if self._timer.isActive() or self._back_timer.isActive():
            self.stop()
        self._curr_test_debug_data.next_event_idx = 0
        self._event_menu.clear_events()
        # self._display.on_startup()
    
    def rerun(self):
        self.clear()
        self.run_or_stop()

    def run_or_stop(self):
        if self._timer.isActive() or self._back_timer.isActive():
            self.stop()
            return
        self.run()

    def run(self):
        if not self.is_test_selected():
            self._message_box.warning('Test is not selected!')
            return
        # disable buttons
        self._tests_menus['main'].setEnabled(False)
        self._button_set.prev_button.setEnabled(False)
        self._button_set.next_button.setEnabled(False)
        self._button_set.run_back_button.setEnabled(False)

        curr_idx = self._curr_test_debug_data.next_event_idx
        if curr_idx >= len(self._curr_test_debug_data.test.events) and curr_idx > 0:
            # RESTART
            self.rerun()
        
        self.next_step()
        self._timer.start(self._settings_editor.get_settings().next_step_delay)
    
    def stop(self):
        self._run_to_event_idx = None
        self._tests_menus['main'].setEnabled(True)
        self._button_set.prev_button.setEnabled(True)
        self._button_set.next_button.setEnabled(True)
        self._button_set.run_back_button.setEnabled(True)
        if self._timer.isActive():
            self._timer.stop()
        elif self._back_timer.isActive():
            self._back_timer.stop()
    
    def run_to_event(self, event_idx: int):
        if self._timer.isActive() or self._back_timer.isActive():
            self.stop()
        if event_idx + 1 == self._curr_test_debug_data.next_event_idx:
            return
        if event_idx < self._curr_test_debug_data.next_event_idx - event_idx:
            self._run_to_event_idx = event_idx
            self.rerun()
        else:
            self._run_to_event_idx = event_idx
            self.run_backwards()
    
    def run_backwards(self):
        if not self.is_test_selected():
            self._message_box.warning('Test is not selected!')
            return
        # disable buttons
        self._tests_menus['main'].setEnabled(False)
        self._button_set.prev_button.setEnabled(False)
        self._button_set.next_button.setEnabled(False)
        self._button_set.run_back_button.setEnabled(False)
        
        self.prev_step()
        self._back_timer.start(self._settings_editor.get_settings().next_step_delay)
    
    def next_step(self):
        if not self.is_test_selected():
            self._message_box.warning('Test is not selected!')
            return
        event_idx = self._curr_test_debug_data.next_event_idx
        if event_idx >= len(self._curr_test_debug_data.test.events):
            if self._timer.isActive():
                self.stop()
            self._message_box.info(f'Last event is reached (#{self._curr_test_debug_data.next_event_idx})')
            return
        if self._run_to_event_idx is not None and event_idx == self._run_to_event_idx + 1:
            self._run_to_event_idx = None
            if self._timer.isActive():
                self.stop()
            return
        event = self._curr_test_debug_data.test.events[
            self._curr_test_debug_data.next_event_idx
        ]
        self._message_box.info(
            f'Event: #{self._curr_test_debug_data.next_event_idx + 1}/'
            f'{len(self._curr_test_debug_data.test.events)}'
        )
        self._curr_test_debug_data.next_event_idx += 1
        self._event_menu.next_event(event)

    def prev_step(self):
        if not self.is_test_selected():
            self._message_box.warning('Test is not selected!')
            return
        event_idx = self._curr_test_debug_data.next_event_idx
        if event_idx == 0:
            if self._back_timer.isActive():
                self.stop()
            self._message_box.info(f'First event reached')
            return
        if self._run_to_event_idx is not None and event_idx == self._run_to_event_idx + 1:
            self._run_to_event_idx = None
            if self._back_timer.isActive():
                self.stop()
            return
        self._curr_test_debug_data.next_event_idx -= 1
        if self._curr_test_debug_data.next_event_idx > 0:
            self._message_box.info(
                f'Event: #{self._curr_test_debug_data.next_event_idx}/'
                f'{len(self._curr_test_debug_data.test.events)}'
            )
        self._event_menu.prev_event()

    def is_test_selected(self):
        return self._curr_test_debug_data is not None

    def show_test_error(self):
        if not self.is_test_selected():
            self._message_box.warning('Test is not selected!')
            return
        self._message_box.error(self._curr_test_debug_data.test.err, custom_level='TEST ERROR')
    
    def show_main_page(self):
        self._central_layout.setCurrentIndex(0)
        self._show_test_error_act.setVisible(False)
    
    def show_test_page(self):
        self._central_layout.setCurrentIndex(1)
    
    def set_settings(self):
        self._settings_editor.edit()


if __name__ == '__main__':
    logger.info('Start application')
    vdeb = VDebugger()
    parser = argparse.ArgumentParser(description='Debug session options')
    parser.add_argument(
        '-l', '--logfile', 
        dest='logfile_path', default='events.log',
        type=str, help='path to file with logs'
    )
    args = parser.parse_args()
    if not path.isfile(args.logfile_path):
        logger.error(f'Unknown path to logfile: {args.logfile_path}')
    else:
        vdeb.main(args.logfile_path)
