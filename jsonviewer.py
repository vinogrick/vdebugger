import typing as t
from PySide2 import QtWidgets, QtCore, QtGui

from static.stylesheets import JSON_VIEWER_STYLESHEET

class JsonViewer(QtWidgets.QTreeWidget):
    def __init__(
            self, 
            json_value, 
            header: str, 
            parent: t.Optional[QtWidgets.QWidget] = None, 
            set_expanded: bool = False,
            expanded_w_ratio: t.Optional[int] = None,
            expanded_h_ratio: t.Optional[int] = None) -> None:
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setHeaderLabel(header)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.reset_value(value=json_value, set_expanded=set_expanded)
        
        self._last_selected_item: t.Optional[QtWidgets.QTreeWidgetItem] = None
        self._last_selected_item_expanded = False

        # preparations for expanding when mouse over 
        self._initial_size = QtCore.QSize(
            self.sizeHint().width(),
            self.visualItemRect(self.topLevelItem(0)).height() * 4  # == 3 rows + header
        )
        self._expanded_w_ratio = expanded_w_ratio
        self._expanded_h_ratio = expanded_h_ratio
        if expanded_w_ratio is not None:
            self.setMinimumWidth(self._initial_size.width())
            self.setMaximumWidth(self._initial_size.width())
        if expanded_h_ratio is not None:
            self.setMinimumHeight(self._initial_size.height())
            self.setMaximumHeight(self._initial_size.height())
        
        self.setStyleSheet(JSON_VIEWER_STYLESHEET)
        
    def _fill_item(self, item, value):
        if value is None:
            return
        elif isinstance(value, dict):
            for key, val in sorted(value.items()):
                if isinstance(val, (int, float, str)):
                    self._new_item(item, f'{key}: [{type(val).__name__}] = {val}')
                else:
                    self._new_item(item, f'{key}: [{type(val).__name__}]', val)
        elif isinstance(value, (list, tuple)):
            for idx, val in enumerate(value):
                if isinstance(val, (int, float, str)):
                    self._new_item(item, f'{idx}: [{type(val).__name__}] = {val}')
                else:
                    self._new_item(item, f'{idx}: [{type(val).__name__}]', val)
        else:
            self._new_item(item, str(value))

    def _new_item(self, parent, text, value=None):
        child = QtWidgets.QTreeWidgetItem([text])
        self._fill_item(child, value)
        parent.addChild(child)
    
    def reset_value(self, value: dict, set_expanded: bool = False):
        self.clear()
        self._fill_item(self.invisibleRootItem(), value)
        if set_expanded:
            self.expandAll()

    def enterEvent(self, event: QtCore.QEvent) -> None:
        if self._expanded_w_ratio is not None:
            self.setMaximumWidth(self._initial_size.width() * self._expanded_w_ratio)
            self.setMinimumWidth(self._initial_size.width() * self._expanded_w_ratio)
        if self._expanded_h_ratio is not None:
            self.setMaximumHeight(self._initial_size.height() * self._expanded_h_ratio)
            self.setMinimumHeight(self._initial_size.height() * self._expanded_h_ratio)
        return super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if self._expanded_w_ratio is not None:
            self.setMinimumWidth(self._initial_size.width())
            self.setMaximumWidth(self._initial_size.width())
        if self._expanded_h_ratio is not None:
            self.setMinimumHeight(self._initial_size.height())
            self.setMaximumHeight(self._initial_size.height())
        return super().leaveEvent(event)
    
    def collapseRecursively(self, item: QtWidgets.QTreeWidgetItem):
        for child_idx in range(item.childCount()):
            self.collapseRecursively(item.child(child_idx))
        self.collapseItem(item)
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.RightButton:
            item = self.selectedItems()[0]
            if self._last_selected_item != item:
                if item.isExpanded():
                    self.collapseRecursively(item)
                    self._last_selected_item_expanded = False
                else:
                    self.expandRecursively(self.indexFromItem(item))
                    self._last_selected_item_expanded = True
                self._last_selected_item = item
            elif self._last_selected_item_expanded:
                self.collapseRecursively(item)
                self._last_selected_item_expanded = False
            else:
                self.expandRecursively(self.indexFromItem(self._last_selected_item))
                self._last_selected_item_expanded = True
        return super().mouseReleaseEvent(event)
