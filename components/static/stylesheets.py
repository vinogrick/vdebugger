from components.static.const import PICS_PATH

JSON_VIEWER_STYLESHEET = '''
QTreeWidget {
    border: 3px solid black;
    border-radius: 10px;
    background-color: white;
    color: black;
}

QTreeWidget::branch:has-siblings:!adjoins-item {
    border-image: url(%(vline)s) 0;
}

QTreeWidget::branch:has-siblings:adjoins-item {
    border-image: url(%(branch_more)s) 0;
}

QTreeWidget::branch:!has-siblings:adjoins-item {
    border-image: url(%(branch_end)s) 0;
}
''' % {
    'vline': f'{PICS_PATH}/vline.png',
    'branch_more': f'{PICS_PATH}/branch-more.png',
    'branch_end': f'{PICS_PATH}/branch-end.png',
}

STARTUP_PAGE_STYLESHEET = '''
QPushButton {
    border: 1px solid grey;
    border-radius: 10px;
    color: black;
}
QPushButton:hover {
    background-color: grey;
}
QPushButton:pressed#PASSED {
    background-color: green;
}
QPushButton:pressed#FAILED {
    background-color: red;
}

QScrollArea#PASSED {
    border: 3px solid green;
    border-radius: 3px;
}
QScrollArea#FAILED {
    border: 3px solid red;
    border-radius: 3px;
}

QScrollBar:vertical {
    background: white;
}
QScrollBar::handle:vertical {         
    border: 0px solid black;
    border-radius: 5px;
    background-color: grey;
}
QScrollBar::add-line:vertical {       
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:vertical {
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
'''

BUTTON_SET_STYLESHEET = '''
QPushButton {
    border: 1px solid grey;
    border-radius: 10px;
    padding-left: 10px;
    padding-right: 10px;
}
QPushButton:hover {
    background-color: grey;
}
QPushButton:pressed {
    background-color: green;
}
'''

SETTINGS_EDITOR_STYLESHEET = '''
QPushButton {
    border: 1px solid grey;
    border-radius: 10px;
    padding-left: 10px;
    padding-right: 10px;
}
QPushButton:hover {
    background-color: grey;
}
QPushButton:pressed {
    background-color: green;
}
'''

MENU_BAR_STYLESHEET = '''
QMenuBar::item:selected {
    background-color: grey
}
QMenuBar::item:pressed {
    background-color: green
}
'''

NODE_INFO_DISPLAY_STYLESHEET = '''
QComboBox {
    border: 1px solid black;
    border-radius: 4px;
}
'''