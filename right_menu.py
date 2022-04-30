from PySide2 import QtCore, QtWidgets, QtGui
import typing as t
from static.const import EventType, OnMouseEventColor
from static.const import STATIC_PATH, EVENT_STEP_TO_ANIM_STEP_RATIO, ENVELOPE_STEPS_COUNT
from util import DebuggerSettings, Event
from nodedisplay import CentralDisplay
from jsonviewer import JsonViewer
from internal_logger import getLogger

logger = getLogger('right_menu')

DISPLAYED_EVENT_GRID = (
    (1, 0, 1, 1),
    (0, 1, 3, 3)
)


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

        # can hide only when this counter = 0
        self._show_counter = 0
        self._select_counter = 0
        self._is_pinned = False  # == selected by left click on it
        self._color = None  # TODO: add autodetect
    
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
        if self._is_pinned:
            self.deselect()
            self._is_pinned = False
        else:
            self.select()
            self._is_pinned = True
        return super().mousePressEvent(event)
    
    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.select()
        return super().enterEvent(event)
    
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.deselect()
        return super().leaveEvent(event)


class DisplayedMsgSend(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, debugger_settings: DebuggerSettings, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --> {event.data["dst"]} | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Message data", self)
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
        self._debugger_settings = debugger_settings
    
    def _show(self):
        self.draw_line()
    
    def _hide(self):
        self.remove_line()
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()
        self._line.setPen(QtGui.QPen(QtGui.QColor('red'), 3))
        self._line.setZValue(1)  # this brings line to the top of all other items to be seen
    
    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self._line.setPen(QtGui.QPen(QtGui.QColor(self._color), 3))
        self._line.setZValue(0)
        self.hide()
    
    def draw_line(self):
        if self._line is not None:
            logger.warning(f"Line already drawn {self._event.data['src']} --> {self._event.data['dst']}")  # TODO: remove this
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
        self._timer.start(self._debugger_settings.next_step_delay / EVENT_STEP_TO_ANIM_STEP_RATIO)
    
    def remove_line(self):
        if self._line is None:
            logger.warning(f"Line already removed {self._event.data['src']} --> {self._event.data['dst']}")  # TODO: remove this
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
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} <-- {event.data["src"]} | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Message data", self)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_RECEIVE
    
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
            logger.warning(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
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
            logger.warning(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._line = None


class DisplayedMsgLocal(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} >>> local | {event.data["msg"]["type"]}'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Message data", self)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.LOCAL_MESSAGE

    def _show(self):
        self._display.displayed_nodes[self._event.data['dst']].show_border()
        self._display.displayed_nodes[self._event.data['dst']].show_local_user()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['dst']].hide_border()
        self._display.displayed_nodes[self._event.data['dst']].hide_local_user()
    

class DisplayedMsgDrop(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)

        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --x {event.data["dst"]} '
            f'| {event.data["msg"]["type"]}\n(Dropped)'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Message data", self)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/cross.png')).scaledToWidth(node_icon_size[0] // 1.5)
        self._cross_size = (pixmap.width(), pixmap.height())
        self._cross = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_DROPPED
    
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
            logger.warning(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
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
        cross_pos = self.calc_cross_position()
        self._cross.setPos(cross_pos[0], cross_pos[1])
        self._display.scene().addItem(self._cross)
    
    def remove_line(self):
        if self._line is None:
            logger.warning(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._cross)
        self._line = None
    
    def calc_cross_position(self):
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
        return (
            src_x + (dst_x - src_x) / 2 - self._cross_size[0] // 2,
            src_y + (dst_y - src_y) / 2 - self._cross_size[1] // 2
        )


class DisplayedMsgDiscard(DisplayedEvent):
    # TODO: add caption to __init__ and unite drop/discard?
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)

        caption = (
            f'{event.data["ts"]:.3f} | {event.data["src"]} --x {event.data["dst"]} '
            f'| {event.data["msg"]["type"]}\n(Discarded)'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(event.data['msg']['data'], "Message data", self)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        node_icon_size = self._display.get_node_icon_size()
        pixmap = QtGui.QPixmap(QtGui.QImage(f'{STATIC_PATH}/pics/cross.png')).scaledToWidth(node_icon_size[0] // 1.5)
        self._cross_size = (pixmap.width(), pixmap.height())
        self._cross = QtWidgets.QGraphicsPixmapItem(pixmap)

        self._line: t.Optional[QtWidgets.QGraphicsLineItem] = None
        self._color: str = OnMouseEventColor.MESSAGE_DROPPED
    
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
            logger.warning(f"Line already drawn {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
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
        cross_pos = self.calc_cross_position()
        self._cross.setPos(cross_pos[0], cross_pos[1])
        self._display.scene().addItem(self._cross)
    
    def remove_line(self):
        if self._line is None:
            logger.warning(f"Line already removed {self._event.data['dst']} <-- {self._event.data['src']}")  # TODO: remove this
            return
        src_node, dst_node = (
            self._display.displayed_nodes[self._event.data['src']],
            self._display.displayed_nodes[self._event.data['dst']]
        )
        src_node.update_conn_counter(-1)
        dst_node.update_conn_counter(-1)

        self._display.scene().removeItem(self._line)
        self._display.scene().removeItem(self._cross)
        self._line = None
    
    def calc_cross_position(self):
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
        return (
            src_x + (dst_x - src_x) / 2 - self._cross_size[0] // 2,
            src_y + (dst_y - src_y) / 2 - self._cross_size[1] // 2
        )


class DisplayedTimerFired(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["dst"]} !-- timer'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer({'name': event.data['name']}, "Message data", self, True)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.TIMER_FIRED

    def _show(self):
        self._display.displayed_nodes[self._event.data['dst']].show_border()
        self._display.displayed_nodes[self._event.data['dst']].show_timer()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['dst']].hide_border()
        self._display.displayed_nodes[self._event.data['dst']].show_timer()
    

class DisplayedNodeCrash(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} CRASHED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Message data", self, True)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_CRASHED

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].show_cross()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].hide_cross()
    

class DisplayedNodeRecover(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} RECOVERED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Message data", self, True)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_RECOVERED

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].hide_cross()

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].show_cross()
    

class DisplayedNodeDisconnect(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} DISCONNECTED!'
        )
        self._main_lbl.setText(caption)

        self._msg_viewer = JsonViewer(None, "Message data", self, True)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_DISCONNECTED

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].setOpacity(0.3)

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].setOpacity(1)
    

class DisplayedNodeConnect(DisplayedEvent):
    def __init__(self, event: Event, display: CentralDisplay, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        DisplayedEvent.__init__(self, event, display, parent)
        caption = (
            f'{event.data["ts"]:.3f} | {event.data["node"]} CONNECTED!'
        )
        self._main_lbl = QtWidgets.QLabel(self)
        self._main_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self._main_lbl.setText(caption)
        self._main_layout.addWidget(self._main_lbl, *DISPLAYED_EVENT_GRID[0])

        self._msg_viewer = JsonViewer(None, "Message data", self, True)
        self._main_layout.addWidget(self._msg_viewer, *DISPLAYED_EVENT_GRID[1])

        self._color: str = OnMouseEventColor.NODE_DISCONNECTED

    def _show(self):
        self._display.displayed_nodes[self._event.data['node']].setOpacity(1)

    def _hide(self):
        self._display.displayed_nodes[self._event.data['node']].setOpacity(0.3)
    
    def _select(self):
        self._main_lbl.setStyleSheet(f'background-color: {self._color};')
        self.show()

    def _deselect(self):
        self._main_lbl.setStyleSheet('')
        self.hide()


# TODO: rename to EventMenu
class RightMenu(QtWidgets.QWidget):
    def __init__(self, display: CentralDisplay, debug_settings: DebuggerSettings, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        QtWidgets.QWidget.__init__(self, parent)
        self._debug_settings = debug_settings
        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._events_scroll = QtWidgets.QScrollArea(self, widgetResizable=True)
        # autoscroll down when event is added
        scroll_bar = self._events_scroll.verticalScrollBar()
        scroll_bar.rangeChanged.connect(lambda: scroll_bar.setValue(scroll_bar.maximum()))
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
        # TODO: reorder events as they are declared in .rs file

        if self._last_shown_event is not None:
            # hide prev step event
            self._last_shown_event.hide()
            self._last_shown_event = None
        
        if event is None:
            # n+1 emitted event to remove last shown event
            self.hide_all_events()
            # TODO: not hide node events?
            return
        
        if event.type == EventType.MESSAGE_SEND:
            self._last_shown_event = DisplayedMsgSend(event, self._display, self._debug_settings, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.MESSAGE_RECEIVE:
            self._last_shown_event = DisplayedMsgRcv(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.LOCAL_MESSAGE_SEND:
            self._last_shown_event = DisplayedMsgLocal(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
            
        elif event.type == EventType.LOCAL_MESSAGE_RECEIVE:
            self._last_shown_event = DisplayedMsgLocal(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()

        elif event.type == EventType.MESSAGE_DROPPED:
            self._last_shown_event = DisplayedMsgDrop(event, self._display, self._events_wgt)
            self._event_stack.append(self._last_shown_event)
            self._events_layout.addWidget(
                self._last_shown_event, alignment=QtCore.Qt.AlignTop
            )
            self._last_shown_event.show()
        
        elif event.type == EventType.MESSAGE_DISCARDED:
            self._last_shown_event = DisplayedMsgDiscard(event, self._display, self._events_wgt)
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

        elif event.type == EventType.NODE_CRASHED:
            new_display_event = DisplayedNodeCrash(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()
        
        elif event.type == EventType.NODE_RECOVERED:
            new_display_event = DisplayedNodeRecover(event, self._display, self._events_wgt)
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
        
        elif event.type == EventType.NODE_CONNECTED:
            new_display_event = DisplayedNodeConnect(event, self._display, self._events_wgt)
            self._event_stack.append(new_display_event)
            self._events_layout.addWidget(
                new_display_event, alignment=QtCore.Qt.AlignTop
            )
            new_display_event.show()

        else:
            logger.warning(f'Not implemented handler for event type: {event.type}')
    
    def prev_event(self):
        self._last_shown_event = None

        curr_displayed_event = self._event_stack.pop()
        prev_displayed_event = self._event_stack[-1]
        curr_event = curr_displayed_event.get_underlying_event()
        prev_event = prev_displayed_event.get_underlying_event()

        # 1. process removing current event
        curr_displayed_event._hide()
        if curr_event.type == EventType.MESSAGE_SEND:
            curr_displayed_event.deleteLater()

        elif curr_event.type == EventType.MESSAGE_RECEIVE:
            curr_displayed_event.deleteLater()
        
        # 2. process showing prev_event
        if prev_event.type == EventType.MESSAGE_SEND:
            prev_displayed_event.show()
    
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

