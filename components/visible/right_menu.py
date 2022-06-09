from PySide2 import QtCore, QtWidgets, QtGui
import typing as t

from components.internal.util import Event
from components.internal.internal_logger import getLogger

from components.static.const import EventType, OnMouseEventColor
from components.static.const import STATIC_PATH, EVENT_STEP_TO_ANIM_STEP_RATIO, ENVELOPE_STEPS_COUNT

from components.visible.debsettings import SettingsEditor
from components.visible.jsonviewer import JsonViewer
from components.visible.nodedisplay import CentralDisplay

logger = getLogger('event_menu')

DISPLAYED_EVENT_GRID = (
    (1, 0, 1, 1),
    (0, 1, 3, 3)
)

NULL_EVENT_TYPE = 'None'


class DisplayedEvent(QtWidgets.QWidget):
    '''
    Abstract class.
    '''
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, parent)
        self._event = event
        self._display = display
        self._main_layout = QtWidgets.QGridLayout(self)

        self._main_lbl = QtWidgets.QLabel(self)
        self._main_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self._main_layout.addWidget(self._main_lbl, *DISPLAYED_EVENT_GRID[0])

        self.setLayout(self._main_layout)

        self._show_counter = 0  # can hide only when this counter = 0
        self._select_counter = 0
        self._is_pinned = False  # == selected by left click on it
        self._color = None
    
    def get_underlying_event(self):
        return self._event
    
    def hide_widget(self):
        super().hide()
    
    def show_widget(self):
        super().show()
    
    def show(self):
        if self._show_counter == 0:
            self._show()
        self._show_counter += 1
    
    def hide(self):
        if self._show_counter == 0:
            return
        self._show_counter -= 1
        if self._show_counter == 0:
            self._hide()

    def _show(self):
        pass

    def _hide(self):
        pass

    def select(self):
        if self._select_counter == 0:
            self._select()
        self._select_counter += 1

    def deselect(self):
        if self._select_counter == 0:
            return
        self._select_counter -= 1
        if self._select_counter == 0:
            self._deselect()

    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self.hide()

    def get_underlying_event(self):
        return self._event

    def is_selected(self):
        return self._select_counter > 0
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._is_pinned:
                self.deselect()
                self._is_pinned = False
            else:
                self.select()
                self._is_pinned = True
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self._display.run_to_event(self._event.idx)
        return super().mousePressEvent(event)
    
    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.select()
        return super().enterEvent(event)
    
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.deselect()
        return super().leaveEvent(event)


class DisplayedMsgSend(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, settings_editor: SettingsEditor, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --> {event.data["dst"]} | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_SEND

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/envelope.png')).scaledToWidth(node_icon_size[0] // 2)
        self._envelope_size = (pixmap.width(), pixmap.height())
        self._envelope = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._envelope_positions = self._calc_envelope_positions()
        self._envelope_pos_idx = 0
        
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.advance_envelope)
        self._settings_editor = settings_editor

        # add msg to node info
        self._display.displayed_nodes[event.data['src']].add_sent_msg(event.data)
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        # self._line.setPen(QtGui.QPen(QtGui.QColor(self._color), 3))
        self._line.setZValue(1)  # this brings line to the top of all other items to be seen
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        # self._line.setPen(QtGui.QPen(QtGui.QColor(self._color), 3))
        self._line.setZValue(0)
        self.hide()
    
    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['src']} --> {self._event.data['dst']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )

        self._envelope_positions = self._calc_envelope_positions()
        self._envelope_pos_idx = 0
        self._envelope.setPos(
            self._envelope_positions[0][0],
            self._envelope_positions[0][1]
        )
        self._display.scene().addItem(self._envelope)
        self._timer.start(self._settings_editor.get_settings().next_step_delay / EVENT_STEP_TO_ANIM_STEP_RATIO)
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['src']} --> {self._event.data['dst']}")
            return
        self._timer.stop()
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._envelope)
        self._line = None
    
    def advance_envelope(self):
        self._envelope_pos_idx = (self._envelope_pos_idx + 1) % (ENVELOPE_STEPS_COUNT + 1)
        self._envelope.setPos(
            self._envelope_positions[self._envelope_pos_idx][0],
            self._envelope_positions[self._envelope_pos_idx][1]
        )
    
    def _calc_envelope_positions(self):
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        step_x = (dst_x - src_x) / ENVELOPE_STEPS_COUNT
        step_y = (dst_y - src_y) / ENVELOPE_STEPS_COUNT
        return [
            (
                src_x + step_x * i - self._envelope_size[0] // 2, 
                src_y + step_y * i - self._envelope_size[1] // 2
            )
            for i in range(ENVELOPE_STEPS_COUNT + 1)
        ]


class DisplayedMsgRcv(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, settings_editor: SettingsEditor, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} <-- {event.data["src"]} | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_RECEIVE

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/envelope.png')).scaledToWidth(node_icon_size[0] // 2)
        self._envelope_size = (pixmap.width(), pixmap.height())
        self._envelope = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._envelope_positions = self._calc_envelope_positions()
        self._envelope_pos_idx = 0
        
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.advance_envelope)
        self._settings_editor = settings_editor

        # add msg to node info
        self._display.displayed_nodes[event.data['dst']].add_received_msg(event.data)
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setZValue(1)

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setZValue(0)
        self.hide()

    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )

        self._envelope_positions = self._calc_envelope_positions()
        self._envelope_pos_idx = 0
        self._envelope.setPos(
            self._envelope_positions[0][0],
            self._envelope_positions[0][1]
        )
        self._display.scene().addItem(self._envelope)
        self._timer.start(self._settings_editor.get_settings().next_step_delay / EVENT_STEP_TO_ANIM_STEP_RATIO)
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        self._timer.stop()
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._envelope)
        self._line = None
    
    def advance_envelope(self):
        self._envelope_pos_idx = (self._envelope_pos_idx + 1) % (ENVELOPE_STEPS_COUNT + 1)
        self._envelope.setPos(
            self._envelope_positions[self._envelope_pos_idx][0],
            self._envelope_positions[self._envelope_pos_idx][1]
        )
    
    def _calc_envelope_positions(self):
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        step_x = (dst_x - src_x) / ENVELOPE_STEPS_COUNT
        step_y = (dst_y - src_y) / ENVELOPE_STEPS_COUNT
        return [
            (
                src_x + step_x * i - self._envelope_size[0] // 2, 
                src_y + step_y * i - self._envelope_size[1] // 2
            )
            for i in range(ENVELOPE_STEPS_COUNT + 1)
        ]


class DisplayedMsgSendLocal(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} >>> local | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.LOCAL_MESSAGE

        # add msg to node info
        self._display.displayed_nodes[event.data['dst']].add_local_sent_msg(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['dst']].show_border()
        self._display.displayed_nodes[self._event.data['dst']].show_local_user()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['dst']].hide_border()
        self._display.displayed_nodes[self._event.data['dst']].hide_local_user()


class DisplayedMsgRcvLocal(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} <<< local | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.LOCAL_MESSAGE

        # add msg to node info
        self._display.displayed_nodes[event.data['dst']].add_local_rcv_msg(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['dst']].show_border()
        self._display.displayed_nodes[self._event.data['dst']].show_local_user()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['dst']].hide_border()
        self._display.displayed_nodes[self._event.data['dst']].hide_local_user()
    

class DisplayedMsgDrop(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, settings_editor: SettingsEditor, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)

        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --x {event.data["dst"]} '
            f'| {event.data["msg"]["type"]}\n(Dropped)'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_DROPPED

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/cross.png')).scaledToWidth(node_icon_size[0] // 1.5)
        self._cross_size = (pixmap.width(), pixmap.height())
        self._cross = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._cross_positions = self._calc_cross_positions()
        self._cross_pos_idx = 0
        
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.advance_cross)
        self._settings_editor = settings_editor

    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setZValue(1)
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setZValue(0)
        self.hide()

    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )

        self._cross_positions = self._calc_cross_positions()
        self._cross_pos_idx = 0
        self._cross.setPos(
            self._cross_positions[0][0],
            self._cross_positions[0][1]
        )
        self._display.scene().addItem(self._cross)
        self._timer.start(self._settings_editor.get_settings().next_step_delay / EVENT_STEP_TO_ANIM_STEP_RATIO)
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        self._timer.stop()
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._cross)
        self._line = None
    
    def advance_cross(self):
        self._cross_pos_idx = (self._cross_pos_idx + 1) % (ENVELOPE_STEPS_COUNT + 1)
        self._cross.setPos(
            self._cross_positions[self._cross_pos_idx][0],
            self._cross_positions[self._cross_pos_idx][1]
        )
    
    def _calc_cross_positions(self):
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        step_x = (dst_x - src_x) / ENVELOPE_STEPS_COUNT
        step_y = (dst_y - src_y) / ENVELOPE_STEPS_COUNT
        return [
            (
                src_x + step_x * i - self._cross_size[0] // 2, 
                src_y + step_y * i - self._cross_size[1] // 2
            )
            for i in range(ENVELOPE_STEPS_COUNT + 1)
        ]


class DisplayedMsgDiscard(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, settings_editor: SettingsEditor, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)

        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --x {event.data["dst"]} '
            f'| {event.data["msg"]["type"]}\n(Discarded)'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Data", self, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_DROPPED

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/cross.png')).scaledToWidth(node_icon_size[0] // 1.5)
        self._cross_size = (pixmap.width(), pixmap.height())
        self._cross = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._cross_positions = self._calc_cross_positions()
        self._cross_pos_idx = 0
        
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.advance_cross)
        self._settings_editor = settings_editor
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setZValue(1)

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setZValue(0)
        self.hide()

    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )
        
        self._cross_positions = self._calc_cross_positions()
        self._cross_pos_idx = 0
        self._cross.setPos(
            self._cross_positions[0][0],
            self._cross_positions[0][1]
        )
        self._display.scene().addItem(self._cross)
        self._timer.start(self._settings_editor.get_settings().next_step_delay / EVENT_STEP_TO_ANIM_STEP_RATIO)
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        self._timer.stop()
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._cross)
        self._line = None
    
    def advance_cross(self):
        self._cross_pos_idx = (self._cross_pos_idx + 1) % (ENVELOPE_STEPS_COUNT + 1)
        self._cross.setPos(
            self._cross_positions[self._cross_pos_idx][0],
            self._cross_positions[self._cross_pos_idx][1]
        )
    
    def _calc_cross_positions(self):
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        step_x = (dst_x - src_x) / ENVELOPE_STEPS_COUNT
        step_y = (dst_y - src_y) / ENVELOPE_STEPS_COUNT
        return [
            (
                src_x + step_x * i - self._cross_size[0] // 2, 
                src_y + step_y * i - self._cross_size[1] // 2
            )
            for i in range(ENVELOPE_STEPS_COUNT + 1)
        ]


class DisplayedTimerFired(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} !-- timer'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer({'name': event.data['name']}, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.TIMER_FIRED

        # add timer to node info
        self._display.displayed_nodes[event.data['node']].add_timer_fired(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].show_border()
        self._display.displayed_nodes[self._event.data['node']].show_timer()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].hide_border()
        self._display.displayed_nodes[self._event.data['node']].hide_timer()
    

class DisplayedNodeCrash(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} CRASHED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_CRASHED

        # add to node info
        self._display.displayed_nodes[event.data['node']].add_node_crashed(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].show_cross()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].hide_cross()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self._display.displayed_nodes[self._event.data['node']].show_cross()
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._display.displayed_nodes[self._event.data['node']].hide_cross()
    

class DisplayedNodeRecover(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} RECOVERED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_RECOVERED

        # add to node info
        self._display.displayed_nodes[event.data['node']].add_node_recovered(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].hide_cross()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].show_cross()

    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self._display.displayed_nodes[self._event.data['node']].show_border()
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._display.displayed_nodes[self._event.data['node']].hide_border()
    

class DisplayedNodeDisconnect(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} DISCONNECTED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_DISCONNECTED

        # add to node info
        self._display.displayed_nodes[event.data['node']].add_node_disconnected(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].show_disconnect()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].hide_disconnect()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self._display.displayed_nodes[self._event.data['node']].show_disconnect()
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._display.displayed_nodes[self._event.data['node']].hide_disconnect()


class DisplayedNodeConnect(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} CONNECTED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_DISCONNECTED

        # add to node info
        self._display.displayed_nodes[event.data['node']].add_node_connected(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].hide_disconnect()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].show_disconnect()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self._display.displayed_nodes[self._event.data['node']].show_border()

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._display.displayed_nodes[self._event.data['node']].hide_border()


class DisplayedNodeRestart(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} RESTARTED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_RESTARTED

        # add to node info
        self._display.displayed_nodes[event.data['node']].add_node_restarted(event.data)

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].show_border()
        self._display.displayed_nodes[self._event.data['node']].show_restart_icon()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].hide_border()
        self._display.displayed_nodes[self._event.data['node']].hide_restart_icon()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self.hide()


class DisplayedLinkDisabled(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --> {event.data["dst"]} | LINK DISABLED'
        )
        self._main_lbl.setText(caption)

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.LINK_DISABLED

        # add to node info
        self._display.displayed_nodes[event.data['src']].add_link_disabled(event.data)
        self._display.displayed_nodes[event.data['dst']].add_link_disabled(event.data)
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setZValue(1)

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setZValue(0)
        self.hide()

    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._line = None
    
class DisplayedLinkEnabled(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --> {event.data["dst"]} | LINK ENABLED'
        )
        self._main_lbl.setText(caption)

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.LINK_ENABLED

        # add to node info
        self._display.displayed_nodes[event.data['src']].add_link_enabled(event.data)
        self._display.displayed_nodes[event.data['dst']].add_link_enabled(event.data)
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setZValue(1)

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setZValue(0)
        self.hide()

    def draw_line(self):
        if self._line is not None:
            logger.debug(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(1)
        dst_node.update_conn_counter(1)

        node_icon_size = self._display.get_node_icon_size()
        src_x, src_y = (
            src_node.scenePos().x() + node_icon_size[0] // 2,
            src_node.scenePos().y() + node_icon_size[1] // 2
        )
        dst_x, dst_y = (
            dst_node.scenePos().x() + node_icon_size[0] // 2,
            dst_node.scenePos().y() + node_icon_size[1] // 2
        )
        self._line = self._display.scene().addLine(
            src_x, src_y, dst_x, dst_y, QtGui.QPen(QtGui.QColor(self._color), 3)
        )
    
    def remove_line(self):
        if self._line is None:
            logger.debug(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._line = None


class DisplayedNetworkPartition(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | NETWORK PARTITION'
        )
        self._main_lbl.setText(caption)

        data = {
            "group1": event.data["group1"],
            "group2": event.data["group2"],
        }
        self._msg_viewer = JsonViewer(data, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NETWORK_PARTITION

        # add to node info
        for node_id in event.data['group1']:
            self._display.displayed_nodes[node_id].add_network_partition(event.data)
        for node_id in event.data['group2']:
            self._display.displayed_nodes[node_id].add_network_partition(event.data)
    
    def _show(self):
        for node_id in self._event.data["group1"]:
            self._display.displayed_nodes[node_id].show_partition(1)
        for node_id in self._event.data["group2"]:
            self._display.displayed_nodes[node_id].show_partition(2)

    def _hide(self):
        for node_id in self._event.data["group1"]:
            self._display.displayed_nodes[node_id].hide_partition()
        for node_id in self._event.data["group2"]:
            self._display.displayed_nodes[node_id].hide_partition()


class DisplayedTestEnd(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'TEST ENDED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Data", self, True, expanded_h_ratio=3)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.TEST_END


class EventMenu(QtWidgets.QWidget):
    def __init__(self, display: CentralDisplay, settings_editor: SettingsEditor, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, parent)
        self._settings_editor = settings_editor
        self._main_layout = QtWidgets.QVBoxLayout(self)

        # filter list
        self._event_filter = QtWidgets.QWidget(self)
        self._event_filter_layout = QtWidgets.QHBoxLayout(self._event_filter)
        self._event_filter_lbl = QtWidgets.QLabel('Filter by: ', self._event_filter)
        self._filter_list = QtWidgets.QComboBox(self._event_filter)
        for type in [
            NULL_EVENT_TYPE,
            *list(EventType)
        ]:
            self._filter_list.addItem(type)
        self._filter_list.currentTextChanged.connect(self.filter_value_changed)
        self._current_filter_value = self._filter_list.currentText()
        self._event_filter_layout.addWidget(self._event_filter_lbl)
        self._event_filter_layout.addWidget(self._filter_list)
        self._event_filter.setLayout(self._event_filter_layout)
        self._main_layout.addWidget(self._event_filter)

        # events scroll area
        self._events_scroll = QtWidgets.QScrollArea(self, widgetResizable=True)
        self._scroll_bar = self._events_scroll.verticalScrollBar()
        self._force_prevent_scrolling = True
        self._scroll_bar.rangeChanged.connect(self.scroll_events_down)  # auto scroll when content changes
        # self._events_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self._events_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._events_wgt = QtWidgets.QWidget(self)
        self._events_layout = QtWidgets.QVBoxLayout(self._events_wgt)
        self._events_layout.addStretch(1)
        self._events_wgt.setLayout(self._events_layout)
        self._events_scroll.setWidget(self._events_wgt)
        self._main_layout.addWidget(self._events_scroll)
        
        self.setLayout(self._main_layout)

        self._last_shown_event: DisplayedEvent = None
        self._display = display

        # {node_id: crash_event}
        self._crash_node_events: t.Dict[str, DisplayedNodeCrash] = {}
        self._disconnect_node_events: t.Dict[str, DisplayedNodeDisconnect] = {}

        self._event_stack: t.List[DisplayedEvent] = []
    
    def next_event(self, event: Event):
        self._filter_list.setCurrentIndex(0)  # show all events for better experience

        self._force_prevent_scrolling = False

        if self._last_shown_event is not None:
            # hide prev step event
            self._last_shown_event.hide()
            self._last_shown_event = None
        
        if not self._event_stack:
            # first call to next event --> add dummy event to stack
            self._event_stack.append(None)
        
        if event.type == EventType.MESSAGE_SEND:
            self._last_shown_event = DisplayedMsgSend(event, self._display, self._settings_editor, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.MESSAGE_RECEIVE:
            self._last_shown_event = DisplayedMsgRcv(event, self._display, self._settings_editor, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.LOCAL_MESSAGE_SEND:
            self._last_shown_event = DisplayedMsgSendLocal(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
            
        elif event.type == EventType.LOCAL_MESSAGE_RECEIVE:
            self._last_shown_event = DisplayedMsgRcvLocal(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.MESSAGE_DROPPED:
            self._last_shown_event = DisplayedMsgDrop(event, self._display, self._settings_editor, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.MESSAGE_DISCARDED:
            self._last_shown_event = DisplayedMsgDiscard(event, self._display, self._settings_editor, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.TIMER_FIRED:
            self._last_shown_event = DisplayedTimerFired(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.NODE_RECOVERED:
            new_display_event = DisplayedNodeRecover(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()

        elif event.type == EventType.NODE_CRASHED:
            new_display_event = DisplayedNodeCrash(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()
        
        elif event.type == EventType.NODE_CONNECTED:
            new_display_event = DisplayedNodeConnect(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()
        
        elif event.type == EventType.NODE_DISCONNECTED:
            new_display_event = DisplayedNodeDisconnect(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()
        
        elif event.type == EventType.NODE_RESTARTED:
            self._last_shown_event = DisplayedNodeRestart(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.LINK_DISABLED:
            self._last_shown_event = DisplayedLinkDisabled(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.LINK_ENABLED:
            self._last_shown_event = DisplayedLinkEnabled(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.NETWORK_PARTITION:
            self._last_shown_event = DisplayedNetworkPartition(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.TEST_END:
            new_display_event = DisplayedTestEnd(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()

        else:
            logger.error(f'Not implemented handler for event type: {event.type}')
            raise RuntimeError('Handler not implemented')
    
    def prev_event(self):
        self._filter_list.setCurrentIndex(0)  # show all events for better experience
        
        if len(self._event_stack) == 1:
            # only first dummy event left
            return
        
        self._force_prevent_scrolling = False
        
        curr_displayed_event = self._event_stack.pop()
        prev_displayed_event = self._event_stack[-1]
        curr_event = curr_displayed_event.get_underlying_event()
        if prev_displayed_event is not None:  # check if this is dummy first event
            prev_event = prev_displayed_event.get_underlying_event()

        # 1. process removing current event
        curr_displayed_event._hide()
        if curr_event.type == EventType.MESSAGE_SEND:
            self._display.displayed_nodes[curr_event.data['src']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.MESSAGE_RECEIVE:
            self._display.displayed_nodes[curr_event.data['dst']].pop_event()
            curr_displayed_event.deleteLater()
        
        elif curr_event.type == EventType.LOCAL_MESSAGE_SEND:
            self._display.displayed_nodes[curr_event.data['dst']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.LOCAL_MESSAGE_RECEIVE:
            self._display.displayed_nodes[curr_event.data['dst']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.MESSAGE_DROPPED:
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.MESSAGE_DISCARDED:
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.TIMER_FIRED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NODE_RECOVERED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NODE_RESTARTED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NODE_CRASHED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NODE_CONNECTED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NODE_DISCONNECTED:
            self._display.displayed_nodes[curr_event.data['node']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.LINK_ENABLED:
            self._display.displayed_nodes[curr_event.data['src']].pop_event()
            self._display.displayed_nodes[curr_event.data['dst']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.LINK_DISABLED:
            self._display.displayed_nodes[curr_event.data['src']].pop_event()
            self._display.displayed_nodes[curr_event.data['dst']].pop_event()
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.NETWORK_PARTITION:
            for node_id in curr_event.data['group1']:
                self._display.displayed_nodes[node_id].pop_event()
            for node_id in curr_event.data['group2']:
                self._display.displayed_nodes[node_id].pop_event()
            curr_displayed_event.deleteLater()
        
        elif curr_event.type == EventType.TEST_END:
            curr_displayed_event.deleteLater()

        else:
            logger.error(f'Not implemented handler for event type: {curr_event.type}')
            raise RuntimeError('Handler not implemented')
        
        if prev_displayed_event is None:
            # nothing to do with dummy event
            return

        # 2. process showing prev_event
        if prev_event.type == EventType.MESSAGE_SEND:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.MESSAGE_RECEIVE:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()
        
        elif prev_event.type == EventType.LOCAL_MESSAGE_SEND:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.LOCAL_MESSAGE_RECEIVE:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.MESSAGE_DROPPED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.MESSAGE_DISCARDED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.TIMER_FIRED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.NODE_RECOVERED:
            prev_displayed_event.show()

        elif prev_event.type == EventType.NODE_RESTARTED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.NODE_CRASHED:
            prev_displayed_event.show()

        elif prev_event.type == EventType.NODE_CONNECTED:
            prev_displayed_event.show()

        elif prev_event.type == EventType.NODE_DISCONNECTED:
            prev_displayed_event.show()

        elif prev_event.type == EventType.LINK_ENABLED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.LINK_DISABLED:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        elif prev_event.type == EventType.NETWORK_PARTITION:
            self._last_shown_event = prev_displayed_event
            prev_displayed_event.show()

        else:
            logger.error(f'Not implemented handler for event type: {prev_event.type}')
            raise RuntimeError('Handler not implemented')
    
    def scroll_events_down(self):
        if self._force_prevent_scrolling:
            # to prevent scrolling when expanding msg info viewer
            return
        self._force_prevent_scrolling = True
        self._scroll_bar.setValue(self._scroll_bar.maximum())
    
    def clear_events(self):
        self._last_shown_event = None
        self._crash_node_events.clear()
        self._disconnect_node_events.clear()
        layout = self._events_layout
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item._hide()  # force hide
                item.deleteLater()
    
    def hide_all_events(self):
        if self._last_shown_event is not None:
            self._last_shown_event._hide()
        layout = self._events_layout
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item._hide()  # force hide
    
    def filter_value_changed(self):
        filter_type = self._filter_list.currentText()
        if self._current_filter_value == filter_type:
            return
        self._current_filter_value = filter_type
        for event in self._event_stack:
            if event is None:
                continue
            if event.get_underlying_event().type == filter_type or filter_type == NULL_EVENT_TYPE:
                event.show_widget()
            else:
                event.hide_widget()
