import sys
import os
import re
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import nuke
import nukescripts

# Valid file format
VALID_IMAGE_EXTENSIONS = {".jpg", ".png", ".dpx", ".exr"}
VALID_VIDEO_EXTENSIONS = {".mov"}
MAX_SELECTED_FOLDERS = 100  # Limit the number of selected folders

class FileBrowser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FileBrowser, self).__init__(parent)

        #self.setWindowTitle("Nuke File Browser - Multi Folder Selection")
        #self.setGeometry(100, 100, 800, 600)

        # Data model
        self.model = QtGui.QStandardItemModel()

        # TreeView to display folders
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSortingEnabled(True)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree.expanded.connect(self.load_subfolders)
        self.tree.clicked.connect(self.toggle_selection)

        # Enable drag and drop
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.startDrag = self.start_drag

        # Context menu for copying folder path
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Folder path input
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("Enter folder path...")
        self.path_edit.returnPressed.connect(self.navigate_to_path)

        # Refresh button
        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.populate_drives)

        # Load folder into Nuke button
        self.load_button = QtWidgets.QPushButton("Load Selected Folders into Nuke")
        self.load_button.clicked.connect(self.load_selected_folders)

        # Uncheck All button
        self.uncheck_all_button = QtWidgets.QPushButton("Uncheck All")
        self.uncheck_all_button.clicked.connect(self.reset_checkboxes)

        # Status bar showing the number of selected folders
        self.status_label = QtWidgets.QLabel("0 Sequence Folders | 0 MOV Video Folders")

        # Info label to display loaded sequence information
        self.info_label = QtWidgets.QLabel("Load Info:File format is name.####.ext (name_####.ext cannot be used)")
        self.info_label.setAlignment(QtCore.Qt.AlignTop)
        self.info_label.setWordWrap(True)

        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.path_edit)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.tree)
        layout.addWidget(self.status_label)
        layout.addWidget(self.load_button)
        layout.addWidget(self.uncheck_all_button)
        layout.addWidget(self.info_label) # Add info label to layout
        self.setLayout(layout)

        # Dictionary to store the selected/unchecked state of folders
        self.selected_folders = {}

        # Display all drives on startup
        self.populate_drives()

    def show_context_menu(self, position):
        """Shows the context menu for copying folder path"""
        indexes = self.tree.selectedIndexes()
        if indexes:
            menu = QtWidgets.QMenu()
            copy_path_action = menu.addAction("Copy Folder Path")
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action == copy_path_action:
                folder_paths = [self.model.itemFromIndex(index).data(QtCore.Qt.UserRole) for index in indexes]
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText("\n".join(folder_paths))

    def start_drag(self, supportedActions):
        """Starts the drag action - Supports dragging multiple folders"""
        indexes = self.tree.selectedIndexes()
        selected_folder_paths = []

        for index in indexes:
            item = self.model.itemFromIndex(index)
            folder_path = item.data(QtCore.Qt.UserRole)
            # Check if the folder is valid and has been selected (checked)
            if folder_path and (self.has_valid_files(folder_path, VALID_IMAGE_EXTENSIONS) or self.has_valid_files(folder_path, VALID_VIDEO_EXTENSIONS)):
                selected_folder_paths.append(folder_path)

        if selected_folder_paths:
            mime_data = QtCore.QMimeData()
            urls = [QtCore.QUrl.fromLocalFile(folder_path) for folder_path in selected_folder_paths]
            mime_data.setUrls(urls)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(QtCore.Qt.CopyAction)

    def populate_drives(self):
        """Displays the list of drives and resets the status"""
        self.model.clear()
        self.selected_folders.clear()
        self.status_label.setText("0 Sequence Folders | 0 MOV Video Folders")
        drives = self.get_drives()
        for drive in drives:
            item = QtGui.QStandardItem(drive)
            item.setEditable(False)
            item.setData(drive, QtCore.Qt.UserRole)
            self.model.appendRow(item)

            if self.has_subfolders(drive):
                item.appendRow(QtGui.QStandardItem("Loading..."))

    def get_drives(self):
        """Gets the list of system drives"""
        drives = []
        if sys.platform == "win32":
            import string
            from ctypes import windll
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:/")
                bitmask >>= 1
        else:
            drives = ["/"]
        return drives

    def load_subfolders(self, index):
        """Lazy Loading: Only loads subfolders when expanded"""
        item = self.model.itemFromIndex(index)
        folder_path = item.data(QtCore.Qt.UserRole)

        if not folder_path or item.rowCount() == 0:
            return

        item.removeRows(0, item.rowCount())

        # Check access permission
        if not os.access(folder_path, os.R_OK):
            QtWidgets.QMessageBox.warning(self, "Error", f"No access permission for folder: {folder_path}")
            return

        try:
            for entry in sorted(os.listdir(folder_path)):
                full_path = os.path.join(folder_path, entry)
                if os.path.isdir(full_path):
                    sub_item = QtGui.QStandardItem(entry)
                    sub_item.setEditable(False)
                    sub_item.setData(full_path, QtCore.Qt.UserRole)
                    item.appendRow(sub_item)

                    # Check if the folder has Image Sequence or Video MOV
                    has_images = self.has_valid_files(full_path, VALID_IMAGE_EXTENSIONS)
                    has_videos = self.has_valid_files(full_path, VALID_VIDEO_EXTENSIONS)

                    if has_images or has_videos:
                        sub_item.setCheckable(True)
                        sub_item.setCheckState(QtCore.Qt.Unchecked) # Reset checkbox when reloading

                    if self.has_subfolders(full_path):
                        sub_item.appendRow(QtGui.QStandardItem("Loading..."))

        except PermissionError:
            QtWidgets.QMessageBox.warning(self, "Error", f"No access permission for folder: {folder_path}")

    def has_subfolders(self, folder):
        """Checks if the folder has subfolders"""
        try:
            return any(os.path.isdir(os.path.join(folder, entry)) for entry in os.listdir(folder))
        except PermissionError:
            return False

    def has_valid_files(self, folder, valid_extensions):
        """Checks if the folder contains valid files"""
        try:
            return any(file.lower().endswith(tuple(valid_extensions)) for file in os.listdir(folder))
        except PermissionError:
            return False

    def toggle_selection(self, index):
        """Toggles the selected/unchecked state of the folder when the checkbox is clicked"""
        item = self.model.itemFromIndex(index)
        if item and item.isCheckable():
            folder_path = item.data(QtCore.Qt.UserRole)
            if item.checkState() == QtCore.Qt.Checked:
                if len(self.selected_folders) >= MAX_SELECTED_FOLDERS:
                    QtWidgets.QMessageBox.warning(self, "Error", f"You can only select up to {MAX_SELECTED_FOLDERS} folders.")
                    item.setCheckState(QtCore.Qt.Unchecked)
                    return
                self.selected_folders[folder_path] = True
            else:
                self.selected_folders.pop(folder_path, None)

            # Update the status display of the number of selected folders
            image_count = sum(self.has_valid_files(f, VALID_IMAGE_EXTENSIONS) for f in self.selected_folders)
            video_count = sum(self.has_valid_files(f, VALID_VIDEO_EXTENSIONS) for f in self.selected_folders)
            self.status_label.setText(f"{image_count} Sequence Folders | {video_count} MOV Video Folders")

    def reset_checkboxes(self):
        """Resets all checkboxes to unchecked state"""
        def recursive_reset(item):
            if item.isCheckable():
                item.setCheckState(QtCore.Qt.Unchecked)
            for row in range(item.rowCount()):
                recursive_reset(item.child(row))

        for row in range(self.model.rowCount()):
            recursive_reset(self.model.item(row))

        self.selected_folders.clear()
        self.status_label.setText("0 Sequence Folders | 0 MOV Video Folders")

    def load_selected_folders(self):
        """Loads all image sequences and MOV videos into Nuke"""
        if not self.selected_folders:
            QtWidgets.QMessageBox.warning(self, "Error", "No folders selected!")
            return
        
        load_info_text = "Load Info:\n"

        has_invalid_folder = False
        for folder in list(self.selected_folders.keys()): # Iterate over a copy to allow modification
            if not self.has_valid_files(folder, VALID_IMAGE_EXTENSIONS) and not self.has_valid_files(folder, VALID_VIDEO_EXTENSIONS):
                QtWidgets.QMessageBox.warning(self, "Error", f"Folder '{folder}' does not contain valid files.")
                self.selected_folders.pop(folder)
                has_invalid_folder = True

        if has_invalid_folder:
            self.reset_checkboxes()  # Update checkbox status
            return

        for folder in self.selected_folders.keys():
            try:
                if self.has_valid_files(folder, VALID_IMAGE_EXTENSIONS):
                    success, info = self.create_image_sequence_read_node(folder)
                    load_info_text += f"{info}\n"

                if self.has_valid_files(folder, VALID_VIDEO_EXTENSIONS):
                    success, info = self.create_mov_read_node(folder)
                    load_info_text += f"{info}\n"
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred while creating the Read node: {e}")

        # Reset checkboxes and selection after loading
        self.reset_checkboxes()
        self.info_label.setText(load_info_text)

    def create_image_sequence_read_node(self, folder):
        """Creates a Read node for Image Sequence"""
        # Fix the pattern to recognize both ### and #### formats
        files = sorted(f for f in os.listdir(folder) if re.match(r".*\.(\d{3,4})\.(jpg|png|dpx|exr)$", f.lower()))
        if not files:
            return False, f"No image sequence found in '{folder}'"

        # Get the first and last frame numbers based on the number of digits in the pattern
        digits = len(files[0].split(".")[-2])
        firstFrame = int(files[0].split(".")[-2])
        lastFrame = int(files[-1].split(".")[-2])

        base_name, extension = files[0].rsplit(".", 2)[0], files[0].rsplit(".", 1)[-1]
        
        # Create a file pattern based on the number of digits
        file_pattern = f"{base_name}.{'#' * digits}.{extension}"
        imageSequencePath = os.path.join(folder, file_pattern).replace("\\", "/")

        readNode = nuke.createNode("Read")
        readNode["file"].setValue(imageSequencePath)
        readNode["first"].setValue(firstFrame)
        readNode["last"].setValue(lastFrame)
        return True, f"Loaded: {file_pattern} from '{folder}'"

    def create_mov_read_node(self, folder):
        """Creates a Read node for MOV video files in the folder."""
        mov_loaded = False
        for file in os.listdir(folder):
            if file.lower().endswith(".mov"):
                file_path = os.path.join(folder, file).replace("\\", "/")
                read_node = nuke.createNode("Read", inpanel=False)
                read_node["file"].fromUserText(file_path)
                mov_loaded = True
        if mov_loaded:
            return True, f"Loaded MOV files from '{folder}'"
        else:
            return False, f"No MOV files found in '{folder}'"
    def navigate_to_path(self):
        """Displays the folder tree from the entered path"""
        path = self.path_edit.text()
        if not os.path.isdir(path):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid path!")
            return

        self.model.clear()
        self.selected_folders.clear() # Clear selected folders
        self.status_label.setText("0 Sequence Folders | 0 MOV Video Folders") # Reset status label

        def add_item_recursive(parent_item, folder_path):
            """Recursively adds folders and subfolders to the model"""
            # Check access permission
            if not os.access(folder_path, os.R_OK):
                QtWidgets.QMessageBox.warning(self, "Error", f"No access permission for folder: {folder_path}")
                return
            try:
                for entry in sorted(os.listdir(folder_path)):
                    full_path = os.path.join(folder_path, entry)
                    if os.path.isdir(full_path):
                        item = QtGui.QStandardItem(entry)
                        item.setEditable(False)
                        item.setData(full_path, QtCore.Qt.UserRole)
                        parent_item.appendRow(item)

                        has_images = self.has_valid_files(full_path, VALID_IMAGE_EXTENSIONS)
                        has_videos = self.has_valid_files(full_path, VALID_VIDEO_EXTENSIONS)
                        if has_images or has_videos:
                            item.setCheckable(True)

                        if self.has_subfolders(full_path):
                            item.appendRow(QtGui.QStandardItem("Loading...")) # Placeholder for lazy loading
            except PermissionError:
                QtWidgets.QMessageBox.warning(self, "Error", f"No access permission for folder: {folder_path}")

        root_item = QtGui.QStandardItem(path)
        root_item.setEditable(False)
        root_item.setData(path, QtCore.Qt.UserRole)
        self.model.appendRow(root_item)
        add_item_recursive(root_item, path)

        self.tree.expand(self.model.indexFromItem(root_item))
class LoadFolderNuke(QMainWindow):
    """ Tích hợp giao diện chọn thư mục vào Nuke """
    def __init__(self):
        super(LoadFolderNuke, self).__init__()
        self.setWindowTitle("Load Folder Panel")
        self.setGeometry(100, 100, 800, 600)

        # Sử dụng FileBrowser đã được import
        self.file_browser = FileBrowser()
        self.setCentralWidget(self.file_browser)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoadFolderNuke()
    window.show()
    sys.exit(app.exec_())

def create_read_node_from_drop(mime_data, text=None):
    """Creates a Read node from data dropped into Nuke - Supports dropping multiple folders"""
    if mime_data.hasUrls():
        for url in mime_data.urls():
            folder_path = url.toLocalFile()
            # Check if the path is a folder or a file
            if os.path.isdir(folder_path):
                # If it is a folder, check if it is an Image Sequence or Video MOV
                if any(re.match(r".*\.(\d{3,4})\.(jpg|png|dpx|exr)$", f) for f in os.listdir(folder_path)):
                    # Create a Read node for Image Sequence
                    files = sorted(f for f in os.listdir(folder_path) if re.match(r".*\.(\d{3,4})\.(jpg|png|dpx|exr)$", f))
                    
                    # Get the first and last frame numbers based on the number of digits in the pattern
                    digits = len(files[0].split(".")[-2])
                    first_frame = int(files[0].split(".")[-2])
                    last_frame = int(files[-1].split(".")[-2])

                    base_name = files[0].rsplit(".", 2)[0]
                    extension = files[0].rsplit(".", 1)[-1]

                    # Create a file pattern based on the number of digits
                    file_pattern = f"{base_name}.{'#' * digits}.{extension}"
                    image_sequence_path = os.path.join(folder_path, file_pattern).replace("\\", "/")

                    read_node = nuke.createNode("Read")
                    read_node["file"].setValue(image_sequence_path)
                    read_node["first"].setValue(first_frame)
                    read_node["last"].setValue(last_frame)

                elif any(f.lower().endswith(".mov") for f in os.listdir(folder_path)):
                    # Create a Read node for Video MOV
                    for file in os.listdir(folder_path):
                        if file.lower().endswith(".mov"):
                            file_path = os.path.join(folder_path, file).replace("\\", "/")
                            read_node = nuke.createNode("Read", inpanel=False)
                            read_node["file"].fromUserText(file_path)

            elif os.path.isfile(folder_path):
                # If it is a file, create a Read node for that file (if it is a valid format)
                if folder_path.lower().endswith((".jpg", ".png", ".dpx", ".exr", ".mov")):
                     read_node = nuke.createNode("Read", inpanel=False)
                     read_node["file"].fromUserText(folder_path)