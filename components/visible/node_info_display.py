from PySide2 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from enum import Enum
import typing as t

from components.internal.util import Serializable

from components.static.const import EventType
from components.static.stylesheets import NODE_INFO_DISPLAY_STYLESHEET

from components.visible.jsonviewer import JsonViewer

# 7x7
DISPLAY_GRID = (
    (0, 0, 1, 1),  # event type lbl
    (0, 1, 1, 1),  # event type filter
    (1, 0, 4, 2),  # jsonviewer
)

NULL_EVENT_TYPE = 'None'

@dataclass
class NodeEvent(Serializable):
    event_type: EventType

@dataclass
class MsgSentEvent(NodeEvent):
    src: str
    dst: str
    msg: t.Dict[t.Any, t.Any]
    ts: float
    msg_type: t.Optional[str] = None

    @classmethod
    def deserialize(cls, data: t.Dict[t.Any, t.Any]):
        result = cls(**data)
        result.msg_type = result.msg['type']
        result.msg = result.msg['data']
        return result

@dataclass
class MsgReceivedEvent(MsgSentEvent):
    pass

@dataclass
class TimerFiredEvent(Serializable):
    name: str
    node: str
    ts: str

class NodeInfoDisplay(QtWidgets.QWidget):
    def __init__(self, node_id: str, parent: t.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)  # TODO: None to open in new window or not?

        self._parent = parent
        self._node_id = node_id
        self.setWindowTitle(f'Node {node_id} info')
        self._main_layout = QtWidgets.QGridLayout(self)

        self._filter_lbl = QtWidgets.QLabel('Filter by: ', self)
        self._filter_list = QtWidgets.QComboBox(self)
        for type in [
            NULL_EVENT_TYPE,
            EventType.MESSAGE_SEND,
            EventType.MESSAGE_RECEIVE,
            EventType.TIMER_FIRED,
        ]:
            self._filter_list.addItem(type)
        self._filter_list.currentTextChanged.connect(self.filter_value_changed)

        self._viewer = JsonViewer(
            {},
            'Events',
            self,
        )

        self._main_layout.addWidget(self._filter_lbl, *DISPLAY_GRID[0])
        self._main_layout.addWidget(self._filter_list, *DISPLAY_GRID[1])
        self._main_layout.addWidget(self._viewer, *DISPLAY_GRID[2])

        self._events: t.List[NodeEvent] = []

        self.setLayout(self._main_layout)

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlag(QtCore.Qt.Window)
        self.setStyleSheet(NODE_INFO_DISPLAY_STYLESHEET)
        self.resize(parent.width() // 2, parent.height() // 2)

        self._close_shortcut = QtWidgets.QShortcut('Ctrl+W', self)
        self._close_shortcut.activated.connect(self.close)

    def add_sent_msg(self, event_data: dict):
        event_data.update(event_type=EventType.MESSAGE_SEND)
        event = MsgSentEvent.deserialize(event_data)
        name = f'{event.ts:.3f} | {event.src} --> {event.dst} | {event.msg_type}'
        self._viewer.add_value_to_root(name, event.msg)
        self._events.append(event)
        if self._filter_list.currentText() not in [NULL_EVENT_TYPE, EventType.MESSAGE_SEND]:
            self._viewer.hide_root_child_at(len(self._events) - 1)
    
    def add_received_msg(self, event_data: dict):
        event_data.update(event_type=EventType.MESSAGE_RECEIVE)
        event = MsgReceivedEvent.deserialize(event_data)
        name = f'{event.ts:.3f} | {event.src} <-- {event.dst} | {event.msg_type}'
        self._viewer.add_value_to_root(name, event.msg)
        self._events.append(event)
        if self._filter_list.currentText() not in [NULL_EVENT_TYPE, EventType.MESSAGE_RECEIVE]:
            self._viewer.hide_root_child_at(len(self._events) - 1)
    
    def add_timer_fired(self, event_data: dict):
        event_data.update(event_type=EventType.TIMER_FIRED)
        event = TimerFiredEvent.deserialize(event_data)
        name = f'{event.ts:.3f} | {event.node} !-- timer (name: {event.name})'
        self._viewer.add_value_to_root(name, None)
        self._events.append(event)
        if self._filter_list.currentText() not in [NULL_EVENT_TYPE, EventType.TIMER_FIRED]:
            self._viewer.hide_root_child_at(len(self._events) - 1)
    
    def pop_event(self):
        event = self._events.pop()
        event_idx = len(self._events)
        self._viewer.remove_root_child(event_idx)
        return event
    
    def filter_value_changed(self):
        filter_type = self._filter_list.currentText()
        for idx in range(len(self._events)):
            if self._events[idx].event_type == filter_type or filter_type == NULL_EVENT_TYPE:
                self._viewer.show_root_child_at(idx)
            else:
                self._viewer.hide_root_child_at(idx)
