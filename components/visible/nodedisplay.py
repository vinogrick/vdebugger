from PySide2 import QtCore, QtWidgets, QtGui
import math
import typing as t

from components.visible.node_info_display import NodeInfoDisplay

from components.internal.internal_logger import getLogger

from components.static.const import STATIC_PATH, NodePlotRule
from components.static.const import OnMouseEventColor

logger = getLogger('nodedisplay')

# declaration for usage in DisplayedNode
class CentralDisplay(QtWidgets.QGraphicsView):
    pass


class DisplayedNode(QtWidgets.QGraphicsItemGroup):
    ICON_PATH = f"{STATIC_PATH}/pics/node.png"
    ICON_GROUP_1 = f"{STATIC_PATH}/pics/node_group_1.png"
    ICON_GROUP_2 = f"{STATIC_PATH}/pics/node_group_2.png"
    CROSS_PATH = f"{STATIC_PATH}/pics/cross.png"
    LOCAL_USER_PATH = f"{STATIC_PATH}/pics/localuser.png"
    TIMER_PATH = f"{STATIC_PATH}/pics/timer.png"
    RESTART_PATH = f"{STATIC_PATH}/pics/restart.png"

    def __init__(self, node_id: str, size: t.Tuple[int, int], display: CentralDisplay, parent: t.Optional[QtWidgets.QGraphicsItem] = None):
        QtWidgets.QGraphicsItemGroup.__init__(self, parent)
        self._id = node_id
        self._node_size = size
        self._display = display
        
        self._node_pixmap = QtGui.QPixmap(self.ICON_PATH).scaled(size[0], size[1])
        self._node_group_1_pixmap = QtGui.QPixmap(self.ICON_GROUP_1).scaled(size[0], size[1])
        self._node_group_2_pixmap = QtGui.QPixmap(self.ICON_GROUP_2).scaled(size[0], size[1])
        self._node = QtWidgets.QGraphicsPixmapItem(self._node_pixmap)
        self.addToGroup(self._node)

        self._border = display.scene().addRect(
            0, 0, size[0], size[1], QtGui.QPen(QtGui.QColor(OnMouseEventColor.LOCAL_MESSAGE), 4)
        )
        self._border.hide()
        self.addToGroup(self._border)

        pixmap = QtGui.QPixmap(self.CROSS_PATH).scaledToWidth(size[0] * 1.2)
        self._cross_size = (pixmap.width(), pixmap.height())
        self._cross = QtWidgets.QGraphicsPixmapItem(pixmap)
        self._cross.hide()
        self._cross.setPos(size[0] // 2 - pixmap.width() // 2, size[1] // 2 - pixmap.height() // 2)
        self.addToGroup(self._cross)

        self._text = QtWidgets.QGraphicsTextItem(node_id)
        self._text.setFont(QtGui.QFont("Times", 12, QtGui.QFont.Bold))
        self._text.setPos(size[0] // 2 - self._text.boundingRect().width() // 2, size[1])
        self.addToGroup(self._text)

        pixmap = QtGui.QPixmap(self.LOCAL_USER_PATH).scaledToWidth(size[0] * 0.7)
        self._local_user_size = (pixmap.width(), pixmap.height())
        self._local_user = QtWidgets.QGraphicsPixmapItem(pixmap)
        self._local_user.setPos(-pixmap.width(), -pixmap.height())
        self._local_user.hide()
        self.addToGroup(self._local_user)

        pixmap = QtGui.QPixmap(self.TIMER_PATH).scaledToHeight(self._local_user_size[1])
        self.timer_size = (pixmap.width(), pixmap.height())
        self._timer = QtWidgets.QGraphicsPixmapItem(pixmap)
        self._timer.setPos(size[0], -pixmap.height())
        self._timer.hide()
        self.addToGroup(self._timer)

        pixmap = QtGui.QPixmap(self.RESTART_PATH).scaledToHeight(self._local_user_size[1])
        self.restart_size = (pixmap.width(), pixmap.height())
        self._restart_icon = QtWidgets.QGraphicsPixmapItem(pixmap)
        self._restart_icon.setPos(size[0], -pixmap.height())
        self._restart_icon.hide()
        self.addToGroup(self._restart_icon)
        
        self._info_viewer = NodeInfoDisplay(self._id, self._display)

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self._connections_counter = 0  # for lines, that represent events (disables movement)
        self._border_show_counter = 0  # border can be really hidden only when this counter = 0
        self._local_user_show_counter = 0  # same as border counter for local user
        self._cross_show_counter = 0
        self._timer_show_counter = 0
        self._restart_icon_show_counter = 0
        self._disconnect_show_counter = 0
        self._partition_show_counter = 0
        
    def update_conn_counter(self, val: int):
        assert val in [-1, 1]
        was_zero = (self._connections_counter == 0)
        self._connections_counter += val
        if self._connections_counter < 0:
            logger.error(f'Something went wrong: connections for {self._id} = {self._connections_counter}')
            self._connections_counter = 0
            return
        if self._connections_counter == 0:
            self.setFlags(self.flags() | QtWidgets.QGraphicsItem.ItemIsMovable)
        elif was_zero:
            self.setFlags(self.flags() & ~QtWidgets.QGraphicsItem.ItemIsMovable)
    
    def show_cross(self):
        if self._cross_show_counter == 0:
            self._cross.show()
        self._cross_show_counter += 1
    
    def hide_cross(self):
        self._cross_show_counter = (
            0 if self._cross_show_counter == 0
            else self._cross_show_counter - 1
        )
        if self._cross_show_counter == 0:
            self._cross.hide()
    
    def show_local_user(self):
        if self._local_user_show_counter == 0:
            self._local_user.show()
        self._local_user_show_counter += 1
        
    def hide_local_user(self):
        self._local_user_show_counter = (
            0 if self._local_user_show_counter == 0
            else self._local_user_show_counter - 1
        )
        if self._local_user_show_counter == 0:
            self._local_user.hide()
    
    def show_border(self):
        if self._border_show_counter == 0:
            self._border.show()
        self._border_show_counter += 1

    def hide_border(self):
        self._border_show_counter = (
            0 if self._border_show_counter == 0
            else self._border_show_counter - 1
        )
        if self._border_show_counter == 0:
            self._border.hide()
    
    def show_timer(self):
        if self._timer_show_counter == 0:
            self._timer.show()
        self._timer_show_counter += 1

    def hide_timer(self):
        self._timer_show_counter = (
            0 if self._timer_show_counter == 0
            else self._timer_show_counter - 1
        )
        if self._timer_show_counter == 0:
            self._timer.hide()
    
    def show_restart_icon(self):
        if self._restart_icon_show_counter == 0:
            self._restart_icon.show()
        self._restart_icon_show_counter += 1

    def hide_restart_icon(self):
        self._restart_icon_show_counter = (
            0 if self._restart_icon_show_counter == 0
            else self._restart_icon_show_counter - 1
        )
        if self._restart_icon_show_counter == 0:
            self._restart_icon.hide()
    
    def show_disconnect(self):
        if self._disconnect_show_counter == 0:
            self.setOpacity(0.3)
        self._disconnect_show_counter += 1
    
    def hide_disconnect(self):
        self._disconnect_show_counter = (
            0 if self._disconnect_show_counter == 0
            else self._disconnect_show_counter - 1
        )
        if self._disconnect_show_counter == 0:
            self.setOpacity(1)
    
    def show_partition(self, group: int):
        if self._partition_show_counter == 0:
            if group == 1:
                self._node.setPixmap(self._node_group_1_pixmap)
            else:
                self._node.setPixmap(self._node_group_2_pixmap)
        self._partition_show_counter += 1

    def hide_partition(self):
        self._partition_show_counter = (
            0 if self._partition_show_counter == 0
            else self._partition_show_counter - 1
        )
        if self._partition_show_counter == 0:
            self._node.setPixmap(self._node_pixmap)
    
    def show_info(self):
        self._display.hide_shown_node_info()
        self._display.set_node_with_shown_info(self._id)
        self._info_viewer.show()
    
    def hide_info(self):
        self._display.set_node_with_shown_info(None)
        self._info_viewer.hide()
    
    def is_info_shown(self):
        return not self._info_viewer.isHidden()
    
    def add_received_msg(self, msg: dict):
        self._info_viewer.add_received_msg(msg)

    def add_sent_msg(self, msg: dict):
        self._info_viewer.add_sent_msg(msg)
    
    def add_timer_fired(self, data: dict):
        self._info_viewer.add_timer_fired(data)
    
    def add_local_sent_msg(self, data: dict):
        self._info_viewer.add_local_sent_msg(data)
    
    def add_local_rcv_msg(self, data: dict):
        self._info_viewer.add_local_rcv_msg(data)

    def add_node_recovered(self, data: dict):
        self._info_viewer.add_node_recovered(data)
    
    def add_node_crashed(self, data: dict):
        self._info_viewer.add_node_crashed(data)
    
    def add_node_restarted(self, data: dict):
        self._info_viewer.add_node_restarted(data)
    
    def add_node_disconnected(self, data: dict):
        self._info_viewer.add_node_disconnected(data)

    def add_node_connected(self, data: dict):
        self._info_viewer.add_node_connected(data)
    
    def add_link_disabled(self, data: dict):
        self._info_viewer.add_link_disabled(data)
    
    def add_link_enabled(self, data: dict):
        self._info_viewer.add_link_enabled(data)
    
    def add_network_partition(self, data: dict):
        self._info_viewer.add_network_partition(data)
    
    def pop_event(self):
        return self._info_viewer.pop_event()


class CustomGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent: t.Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
    
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == QtCore.Qt.RightButton:
            items = self.items(event.scenePos())
            for item in items:
                if isinstance(item, DisplayedNode):
                    if item.is_info_shown():
                        item.hide_info()
                    else:
                        item.show_info()
        return super().mouseReleaseEvent(event)


class CentralDisplay(QtWidgets.QGraphicsView):
    def __init__(
        self,
        parent: t.Optional[QtWidgets.QWidget] = None, 
    ) -> None:
        QtWidgets.QGraphicsView.__init__(self, parent)

        self._parent_window = parent
        
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self._scene = CustomGraphicsScene()
        self._scene.setParent(self)
        # self._scene.setBackgroundBrush(QtCore.Qt.green)
        self.setScene(self._scene)
        self.setSceneRect(-1000, -1000, 2000, 2000)
        
        self._node_ids: t.Set[str] = None
        self.displayed_nodes: t.Dict[str, DisplayedNode] = {}
        self._node_icon_size: t.Optional[t.Tuple[int, int]] = None
        self._node_with_shown_info: t.Optional[str] = None

    
    def clear(self):
        self.hide_shown_node_info()
        self._scene.clear()
        self.displayed_nodes.clear()
    
    def set_node_ids(self, node_ids: t.Set[str]):
        self._node_ids = node_ids

    def on_startup(self):
        self.clear()
        self.plot_nodes(self._node_ids)

    def plot_nodes(self, node_ids: t.Set[str], plot_rule: NodePlotRule = NodePlotRule.CIRCLE):
        points = self.calc_node_positions(plot_rule)
        node_size = self.get_node_icon_size()
        if self.is_ids_ints():
            node_ids = sorted(self._node_ids, key=int)
        else:
            node_ids = sorted(self._node_ids)
        for num, node_id in enumerate(node_ids):
            x, y = points[num]
            self.displayed_nodes[node_id] = DisplayedNode(node_id, node_size, self, None)
            self._scene.addItem(self.displayed_nodes[node_id])
            self.displayed_nodes[node_id].setPos(x, y)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if event.modifiers() & QtCore.Qt.ControlModifier:
            if event.delta() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(1/1.2, 1/1.2)
        else:
            super().wheelEvent(event)
    
    def hide_shown_node_info(self):
        if self._node_with_shown_info is None:
            return
        self.displayed_nodes[self._node_with_shown_info].hide_info()
        self._node_with_shown_info = None
    
    def set_node_with_shown_info(self, node_id: str):
        self._node_with_shown_info = node_id
    
    def run_to_event(self, event_idx: int):
        self._parent_window.run_to_event(event_idx)
        
    ##### HELPERS ###
    def calc_node_positions(self, plot_rule: NodePlotRule = NodePlotRule.CIRCLE) -> t.List[t.Tuple[int, int]]:
        # return circled coords
        max_x, max_y = (
            self.width(), self.height()
        )
        node_size = self.get_node_icon_size()
        if plot_rule == NodePlotRule.CIRCLE:
            radius, curr_angle = (
                min(
                    max_x // 2 - node_size[0], 
                    max_y // 2 - node_size[1]
                ), 
                math.pi / 2
            )
            angle_delta = 2 * math.pi / len(self._node_ids)
            center = (0 - node_size[0] // 2, 0 - node_size[1] // 2)
            resulting_points = []
            for i in range(len(self._node_ids)):
                resulting_points.append((
                    center[0] + math.cos(curr_angle) * radius,
                    center[1] - math.sin(curr_angle) * radius,
                ))
                curr_angle -= angle_delta
            return resulting_points
        if plot_rule == NodePlotRule.ROW:
            raise NotImplementedError()
        if plot_rule == NodePlotRule.COLUMN:
            raise NotImplementedError()
    
    def get_node_icon_size(self):
        if self._node_icon_size is None:
            pixmap = QtGui.QPixmap(DisplayedNode.ICON_PATH)
            pixmap = pixmap.scaledToHeight(self.height() // 8)
            self._node_icon_size = (
                pixmap.width(), pixmap.height()
            )
            return self._node_icon_size
        return self._node_icon_size
    
    def is_ids_ints(self):
        return all(
            node_id.isdigit() for node_id in self._node_ids
        )
