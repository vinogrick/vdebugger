import typing as t
from PySide2 import QtWidgets

# TODO: test this class
class JsonViewer(QtWidgets.QTreeWidget):
    def __init__(self, json_value, header: str, parent: t.Optional[QtWidgets.QWidget] = None, set_expanded: bool = False) -> None:
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setHeaderLabel(header)
        self.header().hide()

        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.reset_value(value=json_value, set_expanded=set_expanded)

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
            for val in value:
                text = (str(val) if not isinstance(val, (dict, list, tuple))
                        else f'[{type(val).__name__}]')
                self._new_item(item, text, val)
        else:
            self._new_item(item, str(value))

    def _new_item(self, parent, text, value=None):
        child = QtWidgets.QTreeWidgetItem([text])
        # child.setFlags(child.flags() | QtCore.Qt.ItemIsEditable)
        self._fill_item(child, value)
        parent.addChild(child)
    
    def reset_value(self, value: dict, set_expanded: bool = False):
        self.clear()
        self._fill_item(self.invisibleRootItem(), value)
        if set_expanded:
            self.expandAll()
