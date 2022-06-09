import json
import typing as t
from dataclasses import dataclass, asdict, field
from PySide2 import QtWidgets

from components.static.const import EventType

@dataclass
class Serializable:
    def serialize(self):
        return asdict(self)
    
    @classmethod
    def deserialize(cls, data: t.Dict[t.Any, t.Any]):
        return cls(**data)
    
    def __str__(self):
        return json.dumps(self.serialize(), indent=2)

@dataclass
class Event:
    EVENT_TYPES = [
        val for val in EventType
    ]
    type: str
    data: t.Dict[str, t.Any]
    idx: int

    @staticmethod
    def from_json(json_event: str, idx: int):
        parsed = json.loads(json_event)
        assert parsed['type'] in Event.EVENT_TYPES, f'Got unexpected event type: {parsed["type"]}'
        return Event(
            parsed['type'],
            parsed['data'],
            idx
        )
    
    def to_json(self, indent=None):
        return json.dumps({
            'type': self.type,
            'data': self.data
        }, indent=indent)
    
    def __str__(self):
        return self.to_json()


def make_test_end_event(idx: int):
    return Event(EventType.TEST_END, {}, idx)


@dataclass
class Test:
    class Status:
        PASSED = "PASSED"
        FAILED = "FAILED"

    name: int
    events: t.List[Event]
    status: Status = None
    err: t.Optional[str] = None
    node_ids: t.Set[str] = field(default_factory=set)

    def to_json(self, indent=None):
        return json.dumps({
            'name': self.name,
            'events': [
                {'type': event.type, 'data': event.data} for event in self.events
            ],
            'status': self.status,
            'err': self.err,
            'node_ids': self.node_ids
        }, indent=indent)

    def __str__(self):
        return self.to_json()


@dataclass
class SessionData:
    tests: t.Dict[str, Test]


@dataclass
class TestDebugData:
    test: Test
    next_event_idx: int = 0


@dataclass
class DebuggerSettings(Serializable):
    next_step_delay: int = 200


class FramedGroup(QtWidgets.QFrame):
    def __init__(
            self, 
            widgets: t.Dict[str, QtWidgets.QWidget], 
            layout_cls: t.Union[QtWidgets.QHBoxLayout, QtWidgets.QVBoxLayout], 
            parent: QtWidgets.QWidget = None
    ):
        QtWidgets.QFrame.__init__(self, parent)

        self.setLayout(layout_cls(self))
        self.widgets: t.Dict[str, QtWidgets.QWidget] = {}
        for name, widget in widgets.items():
            self.widgets[name] = widget
            self.layout().addWidget(widget)
