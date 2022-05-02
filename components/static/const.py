from enum import Enum
from pathlib import Path

# CONSTANTS
DEBUGGER_PATH = Path(__file__).parent.parent.parent.resolve()
STATIC_PATH = f'{DEBUGGER_PATH}/components/static'
PICS_PATH = f'{STATIC_PATH}/pics'
SETTINGS_PATH = f'{STATIC_PATH}/settings.json'

EVENT_STEP_TO_ANIM_STEP_RATIO = 5
ENVELOPE_STEPS_COUNT = EVENT_STEP_TO_ANIM_STEP_RATIO - 1

MIN_STEP_DELAY_MS = 10
MAX_STEP_DELAY_MS = 2000

# ENUMS
class NodePlotRule(int, Enum):
    CIRCLE = 0
    ROW = 1
    COLUMN = 2

class EventType(str, Enum):
    MESSAGE_SEND = 'MessageSend'
    MESSAGE_RECEIVE = 'MessageReceive'
    LOCAL_MESSAGE_SEND = 'LocalMessageSend'
    LOCAL_MESSAGE_RECEIVE = 'LocalMessageReceive'
    MESSAGE_DROPPED = 'MessageDropped'
    MESSAGE_DISCARDED = 'MessageDiscarded'
    TIMER_SET = 'TimerSet'
    TIMER_FIRED = 'TimerFired'
    NODE_RECOVERED = 'NodeRecovered'
    NODE_RESTARTED = 'NodeRestarted'
    NODE_CRASHED = 'NodeCrashed'
    NODE_CONNECTED = 'NodeConnected'
    NODE_DISCONNECTED = 'NodeDisconnected'
    LINK_ENABLED = 'LinkEnabled'
    LINK_DISABLED = 'LinkDisabled'
    NETWORK_PARTITION = 'NetworkPartition'

class MsgBoxColors(str, Enum):
    GREEN = 'green'
    YELLOW = '#F98800'
    RED = 'red'

class OnMouseEventColor(str, Enum):
    MESSAGE_SEND = 'green'
    MESSAGE_RECEIVE = 'violet'
    LOCAL_MESSAGE = 'cyan'  # send + receive
    MESSAGE_DROPPED = 'red'
    TIMER_FIRED = 'yellow'
    NODE_CRASHED = 'red'
    NODE_RECOVERED = 'green'
    NODE_DISCONNECTED = 'yellow'
    NODE_CONNECTED = 'green'
