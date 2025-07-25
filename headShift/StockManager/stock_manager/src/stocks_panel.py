# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import os
import json
from functools import partial
from time import time
from sys import version_info

import nuke

from PySide2.QtCore import (Qt, QSortFilterProxyModel, QSize)
from PySide2.QtGui import (QIcon, QStandardItemModel)
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                               QComboBox, QListView, QAbstractItemView, QListWidget, QListWidgetItem, QSpinBox,
                               QMenu, QAction)

from ..nuke_util.nuke_util import get_nuke_path
from .player_panel import slider
from . import indexing


class stock_view(QListWidget):
    def __init__(self, parent=None):
        QListWidget.__init__(self, parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListView.ExtendedSelection)

        style = """
            QTreeWidget::item:selected,
            QListView::item:selected
            {
                background: rgba(255,150,0, .1);
                color: rgb(200, 200, 200);
            }

            QListView::item
            {
                min-height: 30px;
            }
        """

        self.setStyleSheet(style)

        self.context_menu = QMenu(self)

        self.add_stock_action = QAction("Add Stocks", self)
        self.add_stock_action.triggered.connect(self.add_stocks)
        self.context_menu.addAction(self.add_stock_action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        self.context_menu.exec_(self.mapToGlobal(pos))

    def add_stocks(self):
        for item in self.selectedItems():
            filename = self.get_filename(item)
            self.create_read(filename)

    def mouseDoubleClickEvent(self, _):
        filename = self.get_filename(self.currentIndex())
        self.create_read(filename)

    def create_read(self, filename):

        file_path, frame_range = filename.rsplit(' ', 1)
        first_frame, last_frame = frame_range.split('-')

        first_frame = int(first_frame)
        last_frame = int(last_frame)

        nuke.nodes.Read(file=file_path, first=first_frame, last=last_frame)

    def get_filename(self, item):
        item_data = json.loads(item.data(4))

        filename = item_data['path']
        indexed = item_data['indexed']

        if os.path.isdir(os.path.dirname(filename)):
            filename = '{} {}-{}'.format(filename,
                                         item_data['first_frame'], item_data['last_frame'])
        else:
            filename = os.path.join(indexed, nuke.getFileNameList(indexed)[0])

        return filename

    def dragEnterEvent(self, event):
        event.mimeData().setText(self.get_filename(self.currentIndex()))
        event.accept()

    def dropEvent(self, _):
        return False

    def set_view_mode(self, grid_mode):
        mode = QListView.IconMode if grid_mode else QListView.ListMode
        self.setViewMode(mode)

        self.setAcceptDrops(False)

        if version_info.major == 3:
            self.setDragEnabled(True)
            self.setDragDropMode(QAbstractItemView.DragDrop)

        self.setDropIndicatorShown(False)
        self.setAlternatingRowColors(not grid_mode)

        if grid_mode:
            self.setStyleSheet('QLabel {max-height: 0px;}')
        else:
            self.setStyleSheet('QLabel {max-height: 10000px;}')

    def set_size(self, percent):
        min_size = 50
        max_size = 120

        size = ((max_size - min_size) * percent / 100) + min_size
        self.setIconSize(QSize(size, size))


class stocks(QWidget):
    def __init__(self, player, status_bar):
        QWidget.__init__(self)

        self.status_bar = status_bar
        self.player = player
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.viewerModel = QStandardItemModel()
        self.viewerProxyModel = QSortFilterProxyModel()
        self.viewerProxyModel.setSourceModel(self.viewerModel)

        self.list_widget = stock_view()
        self.list_widget.selectionModel().selectionChanged.connect(self.clicked_item)

        filter_layout = QHBoxLayout()
        filter_layout.setMargin(0)
        filter_widget = QWidget()
        filter_widget.setLayout(filter_layout)

        self.index_folder_filter = QComboBox()
        self.index_folder_filter.setToolTip('Indexed Folder Filter')
        self.index_folder_filter.currentTextChanged.connect(
            self.filter_widget_update)

        self.element_filter = QComboBox()
        self.element_filter.setToolTip('Element Filter')
        self.element_filter.currentTextChanged.connect(
            self.filter_widget_update)

        self.type_filter = QComboBox()
        self.type_filter.setToolTip('Type Filter')
        self.type_filter.currentTextChanged.connect(self.filter_widget_update)

        self.search_filter = QLineEdit()
        self.search_filter.textChanged.connect(self.filter_update)
        self.search_filter.setPlaceholderText('Search Element')

        self.stock_filter = QComboBox()
        self.stock_filter.setToolTip('Stock Filter')
        self.stock_filter.addItems(['All', 'Stocks', 'Textures'])
        self.stock_filter.currentTextChanged.connect(self.filter_widget_update)

        filter_layout.addWidget(self.search_filter)
        filter_layout.addWidget(self.stock_filter)
        filter_layout.addWidget(self.index_folder_filter)
        filter_layout.addWidget(self.element_filter)
        filter_layout.addWidget(self.type_filter)

        display_layout = QHBoxLayout()
        display_layout.setMargin(0)
        display_widget = QWidget()
        display_widget.setLayout(display_layout)

        self.size_slider = slider()
        self.size_slider.setToolTip('Display Size')
        self.size_slider.valueChanged.connect(self.set_size)

        self.max_visibility = QSpinBox()
        self.max_visibility.setValue(50)
        self.max_visibility.setMinimum(1)
        self.max_visibility.setMaximum(2500)
        self.max_visibility.setMaximumWidth(100)
        self.max_visibility.setToolTip('Max Visibility: between 1 and 2500')

        self.list_display = QPushButton()
        self.list_display.setCheckable(True)
        self.list_display.clicked.connect(
            partial(self.set_grid_display, False))
        self.list_display.setToolTip('List Display')
        self.list_display.setIcon(
            QIcon('{0}/stock_manager/icons/list.png'.format(get_nuke_path())))

        self.grid_display = QPushButton()
        self.grid_display.setCheckable(True)
        self.grid_display.clicked.connect(partial(self.set_grid_display, True))
        self.grid_display.setToolTip('Grid Display')
        self.grid_display.setIcon(
            QIcon('{0}/stock_manager/icons/grid.png'.format(get_nuke_path())))

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_stocks)
        self.refresh_btn.setToolTip('Refresh Stocks')
        self.refresh_btn.setIcon(
            QIcon('{0}/stock_manager/icons/refresh.png'.format(get_nuke_path())))

        display_layout.addWidget(self.list_display)
        display_layout.addWidget(self.grid_display)
        display_layout.addSpacing(30)
        display_layout.addWidget(self.size_slider)
        display_layout.addSpacing(30)
        display_layout.addWidget(self.max_visibility)
        display_layout.addWidget(self.refresh_btn)

        layout.addWidget(filter_widget)
        layout.addWidget(self.list_widget)
        layout.addWidget(display_widget)

        self.current_size = 0
        self.is_grid_display = False

        self.update_filter = True

        self.refresh_stocks()

    def set_size(self, size, set_slider=False):
        self.current_size = size
        self.list_widget.set_size(size)

        if set_slider:
            self.size_slider.setValue(size)

    def set_grid_display(self, grid):
        self.is_grid_display = grid

        self.grid_display.setChecked(grid)
        self.list_display.setChecked(not grid)
        self.list_widget.set_view_mode(grid)

    def filter_widget_update(self):
        if not self.update_filter:
            return

        self.update_filter = False

        current_folder = self.index_folder_filter.currentText()
        current_element = self.element_filter.currentText()
        current_type = self.type_filter.currentText()
        current_stock = self.stock_filter.currentText()

        self.index_folder_filter.clear()
        self.element_filter.clear()
        self.type_filter.clear()

        folder_items = []
        element_items = []
        type_items = []

        element_stocks = []

        for _, stock in indexing.get_indexed_stocks().items():
            folder_name = os.path.basename(stock['folder'])

            is_texture = stock['frames'] == 1
            if current_stock == 'Textures' and not is_texture:
                continue

            if current_stock == 'Stocks' and is_texture:
                continue

            if not folder_name in folder_items:
                folder_items.append(folder_name)

            if current_folder and not folder_name == current_folder and not current_folder == 'All':
                continue

            element = stock['element'].capitalize()
            if not element in element_items:
                element_items.append(element)

            element_stocks.append(stock)

        if not current_element in element_items:
            current_element = 'All'

        for stock in element_stocks:
            if current_element:
                if not current_element.lower() == stock['element'] and not current_element == 'All':
                    continue

            _type = stock['type'].capitalize()
            if not _type in type_items:
                type_items.append(_type)

        folder_items = sorted(folder_items)
        element_items = sorted(element_items)
        type_items = sorted(type_items)

        folder_items.insert(0, 'All')
        element_items.insert(0, 'All')
        type_items.insert(0, 'All')

        self.index_folder_filter.addItems(folder_items)
        self.element_filter.addItems(element_items)
        self.type_filter.addItems(type_items)

        self.index_folder_filter.setCurrentText(current_folder)
        self.element_filter.setCurrentText(current_element)
        self.type_filter.setCurrentText(current_type)

        self.update_filter = True
        self.filter_update()

    def filter_update(self):
        if not self.update_filter:
            return

        keyword = self.search_filter.text().lower()
        index_folder = self.index_folder_filter.currentText()
        element_stock = self.element_filter.currentText().lower()
        type_stock = self.type_filter.currentText().lower()
        stock_filter = self.stock_filter.currentText().lower()

        total_visibles = 0

        for _, stock in indexing.get_indexed_stocks().items():
            hide = True

            if stock['element'] == element_stock or element_stock == 'all':
                if stock['type'] == type_stock or type_stock == 'all':
                    if index_folder in stock['folder'] or index_folder == 'All':
                        hide = False

            if not hide:
                if (not keyword in stock['element'] and
                    not keyword in stock['type'] and
                        not keyword in stock['name'].lower()):

                    hide = True

            if not hide and not stock_filter == 'all':
                is_texture = stock['frames'] == 1
                if stock_filter == 'textures' and not is_texture:
                    hide = True

                if stock_filter == 'stocks' and is_texture:
                    hide = True

            stock['hide'] = hide

            if not hide:
                total_visibles += 1

            if not 'item' in stock:
                continue

            stock['item'].setHidden(True)

        _max = self.max_visibility.value()
        i = 0
        showed = 0

        self.list_widget.setVisible(False)

        for _, stock in indexing.get_indexed_stocks().items():
            if stock['hide']:
                continue

            i += 1
            if i > _max:
                break

            self.mount_item(stock)
            stock['item'].setHidden(False)
            showed += 1

        self.status_bar.set_visibles_label(showed, total_visibles)
        self.list_widget.setVisible(True)

    def mount_item(self, stock):
        if stock['mounted']:
            return

        stock['mounted'] = True
        indexed = stock['indexed']
        path = stock['path']
        name = stock['name']
        element = stock['element']
        _type = stock['type']
        frames = stock['frames']
        width, height = stock['resolution']
        item = stock['item']

        self.list_widget.addItem(item)

        frame = '{}/{}.jpg'.format(indexing.thumbnails_folder,
                                   os.path.basename(indexed))
        icon = QIcon(frame)
        item.setIcon(icon)

        item_data = {
            'name': name,
            'indexed': indexed,
            'path': path,
            'frames': frames,
            'first_frame': stock['first_frame'],
            'last_frame': stock['last_frame'],
            'element': element,
            'type': _type,
            'resolution': [width, height]
        }
        item.setData(4, json.dumps(item_data))

        tooltip = (
            'Element: {}\n'
            'Type: {}\n'
            'Frames: {}\n'
            'Resolution: {}'

        ).format(
            element.capitalize(),
            _type.capitalize(),
            frames,
            '{} x {}'.format(width, height)
        )
        item.setToolTip(tooltip)

        label = QLabel()

        data_element = '' if element == 'not labeled' else '{} - '.format(
            element.capitalize())
        data_type = '' if _type == 'not labeled' else '{} - '.format(
            _type.capitalize())

        data_text = '<font color="#64C8FA"><b>{}{}</b><i>{}x{}</i></font>'.format(
            data_element, data_type, width, height)

        left_text = '{} - {}'.format(name, data_text)
        right_text = '<font color="#ffbb00"><b>{}</b></font> frames'.format(
            frames)

        if frames == 1:
            right_text = '<font size=4>|||</font>'

        text = '<td style="vertical-align: middle;" width="50%" align="left">{}</td><td width="50%" align="right">{}</td>'.format(
            left_text, right_text)

        label.setStyleSheet(
            'QLabel {margin-left: 2px; margin-right: 5px;}')
        label.setText(text)
        label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)

        label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.list_widget.setItemWidget(item, label)

    def clear_and_refresh(self):
        self.refresh_stocks(True)

    def refresh_stocks(self, clear=False):
        t = time()

        if clear:
            self.list_widget.clear()

        for _, stock in indexing.get_indexed_stocks().items():
            if 'item' in stock and not clear:
                continue

            item = QListWidgetItem()
            stock['mounted'] = False
            stock['item'] = item
            stock['hide'] = True

        self.set_size(self.current_size, True)
        self.set_grid_display(self.is_grid_display)
        self.filter_widget_update()

        print('Refreshed in {} seconds.'.format(round(time() - t, 2)))

    def clicked_item(self):
        item = self.list_widget.currentIndex()

        item_data = json.loads(item.data(4))
        self.status_bar.set_current_stock(item_data)
        self.player.set_path(item_data['name'], item_data['indexed'],
                             item_data['frames'], item_data['resolution'])
