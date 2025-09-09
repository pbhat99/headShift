import nuke
from PySide2 import QtWidgets, QtCore, QtGui

class WriteManager(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(WriteManager, self).__init__(parent)
        self.setWindowTitle("Write Manager")
        self.setMinimumSize(400, 300)
        self.create_widgets()
        self.create_layout()
        self.populate_write_nodes()

    def create_widgets(self):
        self.write_list_widget = QtWidgets.QListWidget()
        self.write_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.write_list_widget.itemDoubleClicked.connect(self.open_write_node_properties)

        self.create_button = QtWidgets.QPushButton("Create Write Node")
        self.create_button.clicked.connect(self.create_write_node)

        self.delete_button = QtWidgets.QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_write_nodes)

        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.populate_write_nodes)

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.write_list_widget)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        main_layout.addLayout(button_layout)

    def populate_write_nodes(self):
        self.write_list_widget.clear()
        for node in nuke.allNodes("Write"):
            self.write_list_widget.addItem(node.name())

    def create_write_node(self):
        nuke.createNode("Write")
        self.populate_write_nodes()

    def open_write_node_properties(self, item):
        node_name = item.text()
        node = nuke.toNode(node_name)
        if node:
            node.showControlPanel()

    def delete_selected_write_nodes(self):
        selected_items = self.write_list_widget.selectedItems()
        if not selected_items:
            return

        reply = QtWidgets.QMessageBox.question(self, 'Delete Write Nodes',
                                               "Are you sure you want to delete the selected write nodes?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            for item in selected_items:
                node_name = item.text()
                node = nuke.toNode(node_name)
                if node:
                    nuke.delete(node)
            self.populate_write_nodes()

def show_write_manager_dialog():
    """
    Opens the Write Manager dialog.
    """
    global write_manager_dialog
    try:
        write_manager_dialog.close()
        write_manager_dialog.deleteLater()
    except:
        pass
    write_manager_dialog = WriteManager()
    write_manager_dialog.show()

# Nuke Menu Integration
# This assumes that this file is loaded by Nuke's init.py or menu.py
# You might want to adjust the menu path as needed.
nuke.menu('Nuke').addCommand('Custom/Write Manager', show_write_manager_dialog, icon='Write.png')