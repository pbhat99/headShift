import os
import re
import subprocess
import sys
import shutil
import nuke
import nukescripts

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
# from PySide2.QtWidgets import QTreeView
# from PySide2.QtGui import QStandardItemModel

import re

class ImageSequenceProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(ImageSequenceProxyModel, self).__init__(parent)
        self._sequences = {}

    def setSourceModel(self, sourceModel):
        super(ImageSequenceProxyModel, self).setSourceModel(sourceModel)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        file_path = self.sourceModel().filePath(source_index)
        file_name = self.sourceModel().fileName(source_index)

        # Show directories
        if self.sourceModel().isDir(source_index):
            return True

        # Check if it's part of a sequence
        match = re.match(r'(.+?)[._](\d+)\.(.+)', file_name)
        if not match:
            return True  # Not a sequence file

        base_name, frame_str, ext = match.groups()
        frame = int(frame_str)

        seq_key = (os.path.dirname(file_path), f"{base_name}.%0{len(frame_str)}d.{ext}")

        if seq_key not in self._sequences:
            self._sequences[seq_key] = {'frames': set(), 'min': float('inf'), 'max': float('-inf'), 'first_path': None}

        if frame not in self._sequences[seq_key]['frames']:
            self._sequences[seq_key]['frames'].add(frame)
            if frame < self._sequences[seq_key]['min']:
                self._sequences[seq_key]['min'] = frame
                self._sequences[seq_key]['first_path'] = file_path
            if frame > self._sequences[seq_key]['max']:
                self._sequences[seq_key]['max'] = frame

        # Only show the first frame of the sequence
        return file_path == self._sequences[seq_key]['first_path']

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            file_path = self.sourceModel().filePath(source_index)
            file_name = self.sourceModel().fileName(source_index)

            match = re.match(r'(.+?)[._](\d+)\.(.+)', file_name)
            if match:
                base_name, frame_str, ext = match.groups()
                seq_key = (os.path.dirname(file_path), f"{base_name}.%0{len(frame_str)}d.{ext}")

                if seq_key in self._sequences:
                    seq_info = self._sequences[seq_key]
                    if file_path == seq_info['first_path']:
                        return f"{base_name}.[{seq_info['min']}-{seq_info['max']}].{ext}"

        return super(ImageSequenceProxyModel, self).data(index, role)

class ProjectBrowser(QWidget):
    appName = 'browser'
    def __init__(self, parent=None):
        super(ProjectBrowser, self).__init__(parent)
        self.setObjectName('browser')
        self.setWindowTitle('Project Browser v1.5')

        self.selected_shot_path = ""
        self.selected_script_path = ""
        self.ProjectsPath = self.getProjectsPath()

        # Main Layout
        self.main_layout = QHBoxLayout(self)
        self.setLayout(self.main_layout)
        self.createLayouts()
        self.createWidgets()
        self.createConnections()

    def getProjectsPath(self):
        if sys.platform == 'win32':
            return "e:\\!Projects"  # Windows
        elif sys.platform == 'linux':
            return "/media/sf_!Projects"  # Linux
        return ""

    def createLayouts(self):
        self.lay_topVert = QVBoxLayout()
        self.lay_bottomVert = QVBoxLayout()
        self.lay_buttonVert = QVBoxLayout()
        self.lay_src = QHBoxLayout()
        self.lay_sel = QGridLayout()
        self.lay_grd_main = QGridLayout()
        self.lay_grd_project = QGridLayout()

        self.main_layout.addLayout(self.lay_topVert)
        self.lay_topVert.addLayout(self.lay_sel)
        self.lay_topVert.addLayout(self.lay_grd_main)
        self.lay_topVert.addLayout(self.lay_src)
        self.lay_sel.addLayout(self.lay_grd_project, 0, 0, 1, 1)
        self.lay_grd_main.addLayout(self.lay_buttonVert, 1, 4, 1, 1)

    def createWidgets(self):
        self.label = QLabel("Projects Directory:")
        self.label1 = QLabel("PROJECTS")
        self.labelReel = QLabel("SEQ")
        self.label2 = QLabel("SHOTS")
        self.label3 = QLabel("SCRIPTS")

        self.ProjectsFolderPath = QLineEdit()
        self.ProjectsFolderPath.setReadOnly(True)
        self.projectPath = QLineEdit()

        self.projects = QListView()
        self.projects_model = QStandardItemModel()
        self.projects.setModel(self.projects_model)
        self.projects.setFixedWidth(200)

        self.reels = QListView()
        self.reels_model = QStandardItemModel()
        self.reels.setModel(self.reels_model)
        self.reels.setFixedWidth(200)

        self.shots = QListView()
        self.shots_model = QStandardItemModel()
        self.shots.setModel(self.shots_model)
        self.shots.setFixedWidth(200)



        # Scripts panel (Tree instead of List)
        self.scripts = QTreeView()
        self.scripts_model = QStandardItemModel()
        self.scripts.setModel(self.scripts_model)
        self.scripts.setHeaderHidden(True)
        self.scripts.setRootIsDecorated(True)  # shows expand/collapse arrows



        self.src = QTabWidget()
        self.src.setFixedHeight(400)

        self.browseButton = QPushButton('Choose')

        self.newProjectButton = QPushButton('New Project')
        self.shotsButton = QPushButton('Create Shots')
        
        self.refreshButton = QPushButton('Refresh')
        self.explButton = QPushButton('Explorer')

        self.locateButton = QPushButton("Locate")
        self.newButton = QPushButton('New')
        self.openButton = QPushButton('Open')
        self.versionButton = QPushButton('VersionUp')
        self.insertButton = QPushButton('Insert')
        self.importButton = QPushButton("Import")

        self.layoutWidgets()

    def layoutWidgets(self):
        # Row 0: Project directory + Choose button
        self.lay_grd_projectPath = QHBoxLayout()
        self.lay_grd_projectPath.addWidget(self.label)
        self.lay_grd_projectPath.addWidget(self.ProjectsFolderPath)
        self.lay_grd_project.addLayout(self.lay_grd_projectPath, 0, 0, 1, 4)

        self.lay_grd_project.addWidget(self.browseButton, 0, 4, 1, 1)

        # Row 1: Toolbar with all buttons
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.addWidget(self.newProjectButton)
        self.toolbar_layout.addWidget(self.shotsButton)

        #self.toolbar_layout.addSpacing(50)
        self.toolbar_layout.addWidget(self.refreshButton)
        self.toolbar_layout.addWidget(self.explButton)

        self.lay_grd_project.addLayout(self.toolbar_layout, 1, 0, 1, 5)


        self.lay_grd_main.addWidget(self.label1, 0, 0, 1, 1)
        self.lay_grd_main.addWidget(self.labelReel, 0, 1, 1, 1)
        self.lay_grd_main.addWidget(self.label2, 0, 2, 1, 1)
        self.lay_grd_main.addWidget(self.label3, 0, 3, 1, 1)
        self.lay_grd_main.addWidget(self.projects, 1, 0, 1, 1)
        self.lay_grd_main.addWidget(self.reels, 1, 1, 1, 1)
        self.lay_grd_main.addWidget(self.shots, 1, 2, 1, 1)
        self.lay_grd_main.addWidget(self.scripts, 1, 3, 1, 1)

        self.lay_buttonVert.addWidget(self.locateButton)
        self.lay_buttonVert.addWidget(self.newButton)
        self.lay_buttonVert.addWidget(self.openButton)
        self.lay_buttonVert.addWidget(self.versionButton)
        self.lay_buttonVert.addWidget(self.insertButton)
        self.lay_buttonVert.addWidget(self.importButton)

        self.lay_src.addWidget(self.src)

    def createConnections(self):
        self.browseButton.clicked.connect(self.browseProjectFolder)
        self.newProjectButton.clicked.connect(self.createNewProject)
        self.shotsButton.clicked.connect(self.createShots)
        
        self.refreshButton.clicked.connect(self.refresh)
        self.explButton.clicked.connect(self.openFileExplorer)

        self.locateButton.clicked.connect(self.locateCurrentScript)
        self.newButton.clicked.connect(self.createNewScriptPanel)
        self.openButton.clicked.connect(self.openScript)
        self.versionButton.clicked.connect(self.versionScript)
        self.insertButton.clicked.connect(self.copyNodesFromScript)
        self.scripts.selectionModel().currentChanged.connect(self.scriptSelected)
        self.importButton.clicked.connect(self.importScriptAsGroup)





    def locateCurrentScript(self):

        current_path = nuke.root().name()
        if not current_path or not os.path.exists(current_path):
            recent_files_path = os.path.join(os.path.expanduser("~"), ".nuke", "recent_files")
            if os.path.exists(recent_files_path):
                with open(recent_files_path, 'r') as f:
                    recent_file_content = f.read().strip()
                
                if recent_file_content:
                    # Get the first line (latest recent file)
                    latest_recent_file = recent_file_content.splitlines()[0].strip()
                    # Remove quotes if present
                    latest_recent_file = latest_recent_file.strip('"')
                    
                    if os.path.exists(latest_recent_file):
                        current_path = latest_recent_file
                    else:
                        QMessageBox.warning(self, "No Script", "No currently open script and latest recent file does not exist.")
                        return
                else:
                    QMessageBox.warning(self, "No Script", "No currently open script and no recent files found.")
                    return
            else:
                QMessageBox.warning(self, "No Script", "No currently open script and recent files list not found.")
                return

        current_path = os.path.normpath(current_path)

        # --- Trim path until parent of 04_shots (project root) ---
        parts = current_path.split(os.sep)
        try:
            shots_index = parts.index("04_shots")
        except ValueError:
            QMessageBox.warning(self, "Invalid Path or wrrong folder structure", "Could not locate 04_shots in script path.")
            return

        project_root = os.sep.join(parts[:shots_index - 1])  # path up to parent of the project folder
        reel_name = parts[shots_index + 1] if len(parts) > shots_index + 1 else None
        shot_name = parts[shots_index + 2] if len(parts) > shots_index + 2 else None
        script_name = os.path.basename(current_path)

        # Set the ProjectsPath and update the QLineEdit before refreshing
        self.ProjectsPath = project_root
        self.ProjectsFolderPath.setText(self.ProjectsPath)

        # --- Refresh with the new ProjectsPath ---
        self.refresh()

        # --- Select project in Projects panel ---
        project_name = parts[shots_index - 1]
        proj_model = self.projects.model()
        proj_matches = proj_model.match(proj_model.index(0, 0), Qt.DisplayRole, project_name, hits=1, flags=Qt.MatchExactly)
        if proj_matches:
            idx = proj_matches[0]
            self.projects.setCurrentIndex(idx)
            self.projects.scrollTo(idx)
        else:
            QMessageBox.warning(self, "Not Found", f"Project {project_name} not found in Projects panel.")
            return

        # --- Select reel in Reels panel ---
        if reel_name:
            reel_model = self.reels.model()
            reel_matches = reel_model.match(reel_model.index(0, 0), Qt.DisplayRole, reel_name, hits=1, flags=Qt.MatchExactly)
            if reel_matches:
                idx = reel_matches[0]
                self.reels.setCurrentIndex(idx)
                self.reels.scrollTo(idx)
            else:
                QMessageBox.warning(self, "Not Found", f"Reel {reel_name} not found in Reels panel.")
                return

        # --- Select shot in Shots panel ---
        if shot_name:
            shot_model = self.shots.model()
            shot_matches = shot_model.match(shot_model.index(0, 0), Qt.DisplayRole, shot_name, hits=1, flags=Qt.MatchExactly)
            if shot_matches:
                idx = shot_matches[0]
                self.shots.setCurrentIndex(idx)
                self.shots.scrollTo(idx)
            else:
                QMessageBox.warning(self, "Not Found", f"Shot {shot_name} not found in Shots panel.")
                return

        # --- Select script in Scripts panel ---
        script_model = self.scripts.model()
        script_matches = script_model.match(script_model.index(0, 0), Qt.DisplayRole, script_name, hits=1, flags=Qt.MatchExactly | Qt.MatchRecursive)
        if script_matches:
            idx = script_matches[0]
            self.scripts.setCurrentIndex(idx)
            self.scripts.scrollTo(idx)
        else:
            QMessageBox.information(self, "Not Found", f"{script_name} not listed in Scripts panel.")








    def createNewProject(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        
        main_layout = QVBoxLayout()
        
        # Input for project name
        project_name_label = QLabel("Project Name:")
        project_name_input = QLineEdit()
        main_layout.addWidget(project_name_label)
        main_layout.addWidget(project_name_input)
        
        # Ok and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(button_box)
        
        dialog.setLayout(main_layout)
        
        # Connect the buttons
        button_box.accepted.connect(lambda: self.confirmNewProject(dialog, project_name_input.text()))
        button_box.rejected.connect(dialog.reject)
        
        dialog.exec_()


    def confirmNewProject(self, dialog, project_name):
        if not project_name.strip():
            QMessageBox.warning(self, "Invalid Input", "Project name cannot be empty.")
            return
        
        # Construct the path for the new project
        new_project_path = os.path.join(self.ProjectsPath, project_name)
        
        if os.path.exists(new_project_path):
            QMessageBox.warning(self, "Project Exists", "A project with this name already exists.")
            return
        
        try:
            # Create the project directory
            os.makedirs(new_project_path)
            
            # Create subfolders inside the project
            subfolders = [
                '00_docs',
                '01_plates',
                '02_editorial',
                '03_elements',
                '04_shots',
                '05_final',
                '00_docs/brief',
                '00_docs/notes',
                '00_docs/storyboard',
                '00_docs/tech',
            ]
            for subfolder in subfolders:
                os.makedirs(os.path.join(new_project_path, subfolder))
                
        except OSError as e:
            QMessageBox.warning(self, "Directory Creation Failed", f"Failed to create project directory or subfolders: {e}")
            return
        
        dialog.accept()
        self.refresh()  # Refresh the list of projects to include the new project




    
    def createShots(self):
        project_path = self.projectPath.text()
        if not project_path:
            QMessageBox.warning(self, "No Project Selected", "Please select a project first.")
            return
    
        plates_dir = os.path.join(project_path, "01_plates")
        shots_dir = os.path.join(project_path, "04_shots")
    
        # Ensure the plates directory exists
        if not self.ensure_directory_exists(plates_dir):
            return    
        # Ensure the shots directory exists
        if not self.ensure_directory_exists(shots_dir):
            return
    
        subfolders = [
            "Photoshop", "maya", "blender", "ae", "mocha", "nuke",
            "render", "render/comp", "render/precomp", "render/paint", "render/roto",
            "Exports", "Exports/cam", "Exports/geo", "Exports/lensDistort",
        ]

        def create_shot_structure(reel_dir, shot_name):
            shot_folder = os.path.join(reel_dir, shot_name)
            if self.ensure_directory_exists(shot_folder):
                for subfolder in subfolders:
                    self.ensure_directory_exists(os.path.join(shot_folder, subfolder))

        # Get reels (directories) from plates_dir
        reels = [d for d in os.listdir(plates_dir) if os.path.isdir(os.path.join(plates_dir, d))]

        # If no reels, check for files and create a default "seq01" reel
        if not reels and any(os.path.isfile(os.path.join(plates_dir, f)) for f in os.listdir(plates_dir)):
            reels = ["seq01"]

        for reel_name in reels:
            reel_dir_in_shots = os.path.join(shots_dir, reel_name)
            self.ensure_directory_exists(reel_dir_in_shots)

            # Create _TEMPLATE shot
            create_shot_structure(reel_dir_in_shots, "_TEMPLATE")

            reel_dir_in_plates = os.path.join(plates_dir, reel_name)
            if os.path.isdir(reel_dir_in_plates):
                # Get shots from the reel directory in plates
                shots_in_reel = os.listdir(reel_dir_in_plates)
                for shot_name_ext in shots_in_reel:
                    shot_name = os.path.splitext(shot_name_ext)[0]
                    create_shot_structure(reel_dir_in_shots, shot_name)
            else: # This handles the case of the default "seq01" reel
                shots_in_reel = [f for f in os.listdir(plates_dir) if os.path.isfile(os.path.join(plates_dir, f))]
                for shot_name_ext in shots_in_reel:
                    shot_name = os.path.splitext(shot_name_ext)[0]
                    create_shot_structure(reel_dir_in_shots, shot_name)


        self.projectSelected(self.projects.currentIndex())

    def ensure_directory_exists(self, directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                return True
            except OSError as e:
                QMessageBox.warning(self, "Directory Creation Failed", f"Failed to create directory '{directory}': {e}")
                return False
        return True





    





    def browseProjectFolder(self):
        
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.ProjectsPath = QFileDialog.getExistingDirectory(self, "Select Projects Folder", "", options=options)
        if self.ProjectsPath:
            self.ProjectsFolderPath.setText(self.ProjectsPath)
        self.refresh()







    def openFileExplorer(self):
        selected_path = None

        # 1. Check for selected script
        script_index = self.scripts.selectionModel().currentIndex()
        if script_index.isValid():
            selected_path = self.scripts_model.data(script_index, Qt.UserRole)
            if selected_path and os.path.exists(selected_path):
                if os.path.isfile(selected_path):
                    selected_path = os.path.dirname(selected_path)

        # 2. Check for selected shot (if no script selected or script path invalid)
        if not selected_path:
            shot_index = self.shots.selectionModel().currentIndex()
            if shot_index.isValid():
                selected_shot_name = self.shots_model.data(shot_index)
                selected_reel = self.reels.currentIndex().data()
                if selected_reel: # Ensure a reel is also selected
                    selected_path = os.path.join(self.projectPath.text(), "04_shots", selected_reel, selected_shot_name)
                    if not os.path.exists(selected_path):
                        selected_path = None # In case the path doesn't exist

        # 3. Check for selected reel (if no shot/script selected or path invalid)
        if not selected_path:
            reel_index = self.reels.currentIndex()
            if reel_index.isValid():
                reel_name = self.reels_model.data(reel_index)
                selected_path = os.path.join(self.projectPath.text(), "04_shots", reel_name)
                if not os.path.exists(selected_path):
                    selected_path = None # In case the path doesn't exist

        # 4. Check for selected project (if no reel/shot/script selected or path invalid)
        if not selected_path:
            project_index = self.projects.currentIndex()
            if project_index.isValid():
                project_name = self.projects_model.data(project_index)
                selected_path = os.path.join(self.ProjectsPath, project_name)
                if not os.path.exists(selected_path):
                    selected_path = None # In case the path doesn't exist

        # 5. Fallback to current project root if nothing specific is selected or valid
        if not selected_path:
            selected_path = self.projectPath.text()

        if selected_path and os.path.exists(selected_path):
            # Normalize path for Windows explorer
            if sys.platform == 'win32':
                selected_path = os.path.normpath(selected_path)

            if sys.platform == 'darwin':
                subprocess.Popen(['open', selected_path])  # macOS
            elif sys.platform == 'win32':
                subprocess.Popen(['explorer', selected_path])  # Windows
            elif sys.platform == 'linux':
                subprocess.Popen(['xdg-open', selected_path])  # Linux
            else:
                QMessageBox.warning(self, "Unsupported Platform", "Opening file explorer is not supported on this platform.")
        else:
            QMessageBox.warning(self, "Location Not Found", "Could not determine a valid location to open.")







    def refresh(self):
        self.ProjectsFolderPath.setText(self.ProjectsPath)
        self.projects_model.clear()
        if os.path.exists(self.ProjectsPath):
            subdirectories = [
                d for d in os.listdir(self.ProjectsPath)
                if os.path.isdir(os.path.join(self.ProjectsPath, d))
            ]
            for directory in subdirectories:
                item = QStandardItem(directory)
                self.projects_model.appendRow(item)

            self.projects.setModel(self.projects_model)
            try:
                self.projects.selectionModel().currentChanged.disconnect(self.projectSelected)
            except Exception:
                pass
            self.projects.selectionModel().currentChanged.connect(self.projectSelected)

            # Auto-select first project if available
            if self.projects_model.rowCount() > 0:
                first_index = self.projects_model.index(0, 0)
                self.projects.setCurrentIndex(first_index)
                self.projectSelected(first_index)
        else:
            QMessageBox.warning(
                self,
                "Directory Not Found",
                f"The projects directory '{self.ProjectsPath}' does not exist."
            )






    def projectSelected(self, index):
        self.reels_model.clear()
        self.shots_model.clear()
        self.scripts_model.clear()
        self.src.clear()

        if index.isValid():
            selected_folder = os.path.join(self.ProjectsPath, self.projects_model.itemFromIndex(index).text())
            if selected_folder:
                self.projectPath.setText(selected_folder)
                reels_folder = os.path.join(selected_folder, "04_shots")
                if os.path.exists(reels_folder) and os.path.isdir(reels_folder):
                    for reel in os.listdir(reels_folder):
                        if os.path.isdir(os.path.join(reels_folder, reel)):
                            self.reels_model.appendRow(QStandardItem(reel))

                # Populate bottom tabs for project selection
                project_path = self.projectPath.text()
                
                # "all" tab (showing content of 04_shots for the project)
                if os.path.exists(reels_folder): # reels_folder is 04_shots
                    self.addSourceTab(reels_folder, "", "all")

                # "plates" tab (showing content of 01_plates for the project)
                plates_project_path = os.path.join(project_path, "01_plates")
                if os.path.exists(plates_project_path):
                    self.addSourceTab(plates_project_path, "", "plates")
                    
                if self.src.count() > 1:
                    self.src.setCurrentIndex(1) # Select "plates" tab if it exists
                elif self.src.count() > 0:
                    self.src.setCurrentIndex(0)

        if self.reels.selectionModel():
            try:
                self.reels.selectionModel().currentChanged.disconnect(self.reelSelected)
            except:
                pass
            self.reels.selectionModel().currentChanged.connect(self.reelSelected)

    def reelSelected(self, index):
        self.shots_model.clear()
        self.scripts_model.clear()
        self.src.clear() # Clear tabs here, as shotSelected will populate them

        reel_item = self.reels_model.itemFromIndex(index)
        if reel_item:
            reel_name = reel_item.text()
            
            # Populate SHOTS panel from 04_shots
            shots_reel_path = os.path.join(self.projectPath.text(), "04_shots", reel_name)
            if os.path.exists(shots_reel_path):
                for shot in os.listdir(shots_reel_path):
                    if os.path.isdir(os.path.join(shots_reel_path, shot)): # Only add directories
                        self.shots_model.appendRow(QStandardItem(shot))

            if self.shots.selectionModel():
                try:
                    self.shots.selectionModel().currentChanged.disconnect(self.shotSelected)
                except:
                    pass
                self.shots.selectionModel().currentChanged.connect(self.shotSelected)

            # Populate bottom tabs
            project_path = self.projectPath.text()
            plates_reel_path = os.path.join(project_path, "01_plates", reel_name)

            # "all" tab (showing content of 04_shots/reel_name)
            if os.path.exists(shots_reel_path):
                self.addSourceTab(shots_reel_path, "", "all")

            # "plates" tab (showing content of 01_plates/reel_name)
            if os.path.exists(plates_reel_path):
                self.addSourceTab(plates_reel_path, "", "plates")
                
            if self.src.count() > 1:
                self.src.setCurrentIndex(1) # Select "plates" tab if it exists
            elif self.src.count() > 0:
                self.src.setCurrentIndex(0)






    def shotSelected(self, index):
        shot_item = self.shots_model.itemFromIndex(index)
        selected_shot = shot_item.text()
        selected_reel = self.reels.currentIndex().data()
        self.selected_shot_path = os.path.join(self.projectPath.text(), "04_shots", selected_reel, selected_shot)
        self.populateScriptsModel(self.selected_shot_path)
        self.updateSourceTabs(self.projectPath.text(), self.selected_shot_path, selected_reel)







    def scriptSelected(self, current, previous=None):
        """Handle script selection. If a group is clicked, auto-select latest version child."""
        if not current.isValid():
            self.selected_script_path = None
            return

        item = self.scripts_model.itemFromIndex(current)
        if not item:
            self.selected_script_path = None
            return

        if item.hasChildren():
            # This is a group item. Get the first child (highest version).
            child_item = item.child(0)
            if child_item:
                fpath = child_item.data(Qt.UserRole)
                if fpath and os.path.exists(fpath):
                    self.selected_script_path = fpath
                else:
                    self.selected_script_path = None
            else:
                self.selected_script_path = None
        else:
            # This is a child item (a specific version).
            fpath = item.data(Qt.UserRole)
            if fpath and os.path.exists(fpath):
                self.selected_script_path = fpath
            else:
                self.selected_script_path = None







    def populateScriptsModel(self, selected_shot_path):
        self.scripts_model.clear()
        self.scripts_model.setHorizontalHeaderLabels(["Scripts"])

        nuke_folder_path = os.path.join(selected_shot_path, "nuke")
        if not os.path.exists(nuke_folder_path):
            return

        nk_files = []
        for file in os.listdir(nuke_folder_path):
            if file.endswith(".nk"):
                nk_files.append(os.path.join(nuke_folder_path, file))

        groups = {}
        for file_path in nk_files:
            file_name = os.path.basename(file_path)
            if "_v" in file_name:
                base, ver = file_name.rsplit("_v", 1)
                ver_num = int(ver.split(".")[0])
                groups.setdefault(base, []).append((ver_num, file_name, file_path))
            else:
                groups.setdefault(file_name, []).append((0, file_name, file_path))

        for base, versions in groups.items():
            versions.sort(key=lambda x: x[0], reverse=True)
            highest_version = versions[0][0]

            # Parent item → bold + suffix with -v###
            parent_item = QStandardItem(f"{base} - v{str(highest_version).zfill(3)}")
            font = QFont()
            font.setBold(True)
            parent_item.setFont(font)
            parent_item.setEditable(False)
            parent_item.setSelectable(True)

            # Add children (all versions)
            for ver, fname, fpath in versions:
                child = QStandardItem(fname)
                child.setEditable(False)
                child.setData(fpath, Qt.UserRole)  # store absolute file path
                parent_item.appendRow(child)

            self.scripts_model.appendRow(parent_item)

        #self.scripts.expandAll()








    def updateSourceTabs(self, project_path, selected_shot_path, selected_reel):
        current_tab_index = self.src.currentIndex()
        self.src.clear()

        # "all" tab
        self.addSourceTab(os.path.dirname(selected_shot_path), os.path.basename(selected_shot_path), "all")

        # "plates" tab
        shot_name = os.path.basename(selected_shot_path)
        plates_shot_folder_path = os.path.join(project_path, "01_plates", selected_reel, shot_name)
        if os.path.exists(plates_shot_folder_path):
            self.addSourceTab(os.path.join(project_path, "01_plates", selected_reel), shot_name, "plates")

        # "render" tab
        render_path = os.path.join(selected_shot_path, "render")
        if os.path.exists(render_path):
            self.addSourceTab(selected_shot_path, "render", "render")

        # "Exports" tab
        exports_path = os.path.join(selected_shot_path, "Exports")
        if os.path.exists(exports_path):
            self.addSourceTab(selected_shot_path, "Exports", "Exports")

        if current_tab_index != -1:
            self.src.setCurrentIndex(current_tab_index)
        else:
            self.src.setCurrentIndex(0)





    def addSourceTab(self, path, directory, tab_name):
        tab_page = QWidget()
        tab_layout = QVBoxLayout()
        file_browser = QTreeView()

        source_model = QFileSystemModel()
        source_model.setRootPath(path)

        proxy_model = ImageSequenceProxyModel()
        proxy_model.setSourceModel(source_model)

        file_browser.setModel(proxy_model)
        file_browser.setRootIndex(proxy_model.mapFromSource(source_model.index(os.path.join(path, directory))))

        file_browser.setColumnWidth(0, 500)
        file_browser.setDragEnabled(True)
        file_browser.setWordWrap(False)
        tab_layout.addWidget(file_browser)
        tab_page.setLayout(tab_layout)
        self.src.addTab(tab_page, tab_name)







    def createNewScriptPanel(self):
        if not self.selected_shot_path:
            QMessageBox.warning(self, "No Shot Selected", "Please select a shot first.")
            return

        # --- Dialog setup ---
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Script")

        main_layout = QVBoxLayout(dialog)

        # --- Row: Task + Assignment + Version ---
        row_layout = QHBoxLayout()

        # Task dropdown
        task_combo = QComboBox(dialog)
        task_combo.addItems(["comp", "precomp", "prep", "roto", "denoise"])
        task_combo.setCurrentIndex(0)  # comp default
        row_layout.addWidget(QLabel("Task:"))
        row_layout.addWidget(task_combo)

        # Assignment input
        assignment_edit = QLineEdit(dialog)
        row_layout.addWidget(QLabel("Assignment:"))
        row_layout.addWidget(assignment_edit)

        # Version input
        version_edit = QLineEdit(dialog)
        version_edit.setFixedWidth(50)
        version_edit.setText("001")
        row_layout.addWidget(QLabel("Version:"))
        row_layout.addWidget(version_edit)

        main_layout.addLayout(row_layout)

        # Preview row: label + yellow filename
        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Preview:"))
        preview_label = QLabel(dialog)
        preview_label.setStyleSheet("color: yellow; font-weight: bold;")
        preview_row.addWidget(preview_label)
        preview_row.addStretch(1)
        main_layout.addLayout(preview_row)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        main_layout.addWidget(button_box)

        # --- Helper: find next available version (no reel prefix) ---
        def get_next_version(task, assignment):
            comp_path = os.path.join(self.selected_shot_path, "nuke")
            if not os.path.exists(comp_path):
                return 1

            shot_name = os.path.basename(self.selected_shot_path)
            if assignment:
                prefix = f"{shot_name}_{task}_{assignment}_v"
            else:
                prefix = f"{shot_name}_{task}_v"

            max_version = 0
            for f in os.listdir(comp_path):
                if f.startswith(prefix) and f.endswith(".nk"):
                    try:
                        ver_num = int(f.split("_v")[-1].split(".")[0])
                        max_version = max(max_version, ver_num)
                    except:
                        pass
            return max_version + 1

        # --- Helper: update preview (auto-increments when task/assignment change) ---
        def update_preview(auto_version=False):
            task = task_combo.currentText()
            assignment = assignment_edit.text().strip()
            version_text = version_edit.text().strip()
            shot_name = os.path.basename(self.selected_shot_path)

            if auto_version:
                next_version = get_next_version(task, assignment)
                version_text = str(next_version).zfill(3)
                version_edit.setText(version_text)

            if not version_text.isdigit():
                version_text = "001"
            version_text = version_text.zfill(3)

            if assignment:
                filename = f"{shot_name}_{task}_{assignment}_v{version_text}.nk"
            else:
                filename = f"{shot_name}_{task}_v{version_text}.nk"

            preview_label.setText(filename)

        # Wire live updates
        task_combo.currentIndexChanged.connect(lambda: update_preview(True))
        assignment_edit.textChanged.connect(lambda: update_preview(True))
        version_edit.textChanged.connect(lambda: update_preview(False))

        # Initialize preview and focus
        update_preview(True)
        assignment_edit.setFocus()

        # --- Actions ---
        def accept():
            task = task_combo.currentText()
            assignment = assignment_edit.text().strip()
            version_text = version_edit.text().strip()
            if not version_text.isdigit():
                version_text = "001"
            version_text = version_text.zfill(3)

            if not assignment:
                QMessageBox.warning(dialog, "Missing Input", "Please enter an assignment name.")
                return

            shot_name = os.path.basename(self.selected_shot_path)
            filename = f"{shot_name}_{task}_{assignment}_v{version_text}.nk"
            new_script_path = os.path.join(self.selected_shot_path, "nuke", filename)
            self.ensure_directory_exists(os.path.dirname(new_script_path))

            nuke.scriptClear()
            nuke.scriptSaveAs(new_script_path)

            self.populateScriptsModel(self.selected_shot_path)
            dialog.accept()

        button_box.accepted.connect(accept)
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()






    





    








    def openScript(self):
        if not self.selected_script_path:
            QMessageBox.warning(self, "No Script Selected", "Please select a script to open.")
            return

        # Step 1: Handle unsaved changes
        if nuke.root().modified():
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("The current script has unsaved changes. What do you want to do?")

            save_btn = msg.addButton("Save", QMessageBox.AcceptRole)
            no_btn = msg.addButton("Don't Save", QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton("cancel", QMessageBox.DestructiveRole)

            msg.setDefaultButton(save_btn)
            msg.exec_()

            if msg.clickedButton() == save_btn:
                nuke.scriptSave()
            elif msg.clickedButton() == no_btn:
                pass
            elif msg.clickedButton() == cancel_btn:
                return

        # Step 2: Ask where to open the selected script
        msg2 = QMessageBox(self)
        msg2.setWindowTitle("Open Script")
        msg2.setText("Where do you want to open this script?")

        same_btn = msg2.addButton("Same Session", QMessageBox.AcceptRole)
        new_inst_btn = msg2.addButton("New Instance", QMessageBox.DestructiveRole)

        msg2.setDefaultButton(same_btn)
        msg2.exec_()

        if msg2.clickedButton() == same_btn:
            # Open in same session
            nuke.scriptClear()
            nuke.scriptOpen(self.selected_script_path)
        elif msg2.clickedButton() == new_inst_btn:
            # Launch new Nuke instance
            import subprocess
            subprocess.Popen([nuke.env["ExecutablePath"], self.selected_script_path])








    def versionScript(self):
        if not self.selected_script_path:
            QMessageBox.warning(self, "No Script Selected", "Please select a script to version up.")
            return
    
        script_dir, script_name = os.path.split(self.selected_script_path)
        name, ext = os.path.splitext(script_name)
    
        # Extract the version number if it exists
        if '_v' in name:
            base_name, version = name.rsplit('_v', 1)
            try:
                current_version = int(version)
            except ValueError:
                QMessageBox.warning(self, "Invalid Version", "The script's version number could not be determined.")
                return
        else:
            base_name = name
            current_version = 0
    
        # Find the next available version number
        new_version = current_version + 1
        new_script_name = f"{base_name}_v{new_version:03d}{ext}"
        new_script_path = os.path.join(script_dir, new_script_name)
    
        while os.path.exists(new_script_path):
            new_version += 1
            new_script_name = f"{base_name}_v{new_version:03d}{ext}"
            new_script_path = os.path.join(script_dir, new_script_name)
    
        # Copy the original script to the new versioned filename
        try:
            shutil.copy(self.selected_script_path, new_script_path)
            print(f"Script versioned up: {new_script_path}")
        except IOError as e:
            QMessageBox.warning(self, "Copy Failed", f"Failed to copy script: {e}")
            return

        self.populateScriptsModel(self.selected_shot_path)
    
        # Optionally, open the new script (adjust this based on your script opening logic)
        self.selected_script_path = new_script_path
        self.openScript()








    def copyNodesFromScript(self):
        if os.path.exists(self.selected_script_path):
            nuke.nodePaste(self.selected_script_path)
        else:
            QMessageBox.warning(self, "Script Not Found", f"The selected script '{self.selected_script_path}' does not exist.")






    # speedyscript
    def importScriptAsGroup(self):
        selected_indexes = self.scripts.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "No Script Selected", "Please select a script to import.")
            return

        item = self.scripts_model.itemFromIndex(selected_indexes[0])
        if not item:
            return

        script_path = None
        if item.hasChildren():
            # This is a group item. Get the first child (highest version).
            child_item = item.child(0)
            if child_item:
                script_path = child_item.data(Qt.UserRole)
        else:
            # This is a child item (a specific version).
            script_path = item.data(Qt.UserRole)

        if not script_path or not os.path.exists(script_path):
            QMessageBox.warning(self, "File Missing", f"Script not found:\n{script_path}")
            return

        try:
            self.importScriptFunction(script_path)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def importScriptFunction(self, filePath):
        size = os.path.getsize(filePath)
        sizeMB = size / (1024*1024)

        if size > 8000000:
            import_ok = nuke.ask(
                f"File is {sizeMB:.1f}MB. Importing could take some seconds.\n"
                f"Do you want to continue?"
            )
            if not import_ok:
                return

        nuke.localization.pauseLocalization()

        group = nuke.createNode("Group")
        fileName = os.path.basename(filePath).replace('.nk', '').replace(' ', '_')

        group.knob('name').setValue("SCRIPT_IMPORTED_" + fileName)
        group.knob('label').setValue(filePath)
        group.knob('note_font_size').setValue(20)
        group.knob('tile_color').setValue(0x99000000)
        group.knob('note_font_color').setValue(4294967041)
        group.knob('note_font').setValue("bold")

        groupNode = nuke.toNode(group.name())
        groupNode.begin()
        nuke.nodePaste(filePath)
        groupNode.end()

        nuke.showDag(groupNode)












# Create and show the custom UI
custom_ui = ProjectBrowser()

# Set the desired width and height for the dialog window
desired_width = 1000
desired_height = 600
screen_geometry = QApplication.desktop().availableGeometry()
x = (screen_geometry.width() - desired_width) / 2 - 600
y = (screen_geometry.height() - desired_height) / 2
# Adjust the minimum size of the dialog's inner layout
custom_ui.setGeometry(x, y, desired_width, desired_height)






nukescripts.registerWidgetAsPanel('ProjectBrowser', 'Project Browser', ProjectBrowser.appName)
