import os
import subprocess
import sys
import shutil
import nuke
import nukescripts

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

class ProjectBrowser(QWidget):
    appName = 'browser'
    def __init__(self, parent=None):
        super(ProjectBrowser, self).__init__(parent)
        self.setObjectName('browser')
        self.setWindowTitle('Project Browser v1.4 - Full Functions Restored')

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

        self.scripts = QListView()
        self.scripts_model = QStandardItemModel()
        self.scripts.setModel(self.scripts_model)

        self.src = QTabWidget()
        self.src.setFixedHeight(400)

        self.browseButton = QPushButton('Choose')
        self.refreshButton = QPushButton('Refresh')
        self.newProjectButton = QPushButton('New Project')
        self.shotsButton = QPushButton('Create Shots')
        self.templateButton = QPushButton('Create Template')

        self.explButton = QPushButton('Explorer')
        self.newButton = QPushButton('New')
        self.openButton = QPushButton('Open')
        self.versionButton = QPushButton('VersionUp')
        self.insertButton = QPushButton('Insert')
        self.clearButton = QPushButton('Clear')

        self.layoutWidgets()

    def layoutWidgets(self):
        # Row 0: Project directory + Choose button
        self.lay_grd_project.addWidget(self.label, 0, 0, 1, 1)
        self.lay_grd_project.addWidget(self.ProjectsFolderPath, 0, 1, 1, 3)
        self.lay_grd_project.addWidget(self.browseButton, 0, 4, 1, 1)

        # Row 1: Toolbar with all buttons
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.addWidget(self.newProjectButton)
        self.toolbar_layout.addWidget(self.shotsButton)
        self.toolbar_layout.addWidget(self.templateButton)
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

        self.lay_buttonVert.addWidget(self.newButton)
        self.lay_buttonVert.addWidget(self.openButton)
        self.lay_buttonVert.addWidget(self.versionButton)
        self.lay_buttonVert.addWidget(self.insertButton)
        self.lay_buttonVert.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.lay_buttonVert.addWidget(self.clearButton)

        self.lay_src.addWidget(self.src)

    def createConnections(self):
        self.browseButton.clicked.connect(self.browseProjectFolder)
        self.refreshButton.clicked.connect(self.refresh)
        self.newProjectButton.clicked.connect(self.createNewProject)
        self.shotsButton.clicked.connect(self.createShots)
        self.templateButton.clicked.connect(self.createTemplateScript)
        self.explButton.clicked.connect(self.openFileExplorer)
        self.newButton.clicked.connect(self.createNewScriptPanel)
        self.openButton.clicked.connect(self.openScript)
        self.versionButton.clicked.connect(self.versionScript)
        self.insertButton.clicked.connect(self.copyNodesFromScript)
        self.clearButton.clicked.connect(self.clearSelection)
        self.scripts.selectionModel().currentChanged.connect(self.scriptSelected)






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
               '00_docs/tech'
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
            "comp", "dmp", "fx", "gfx", "lay", "lgt", "mm", "paint", "roto",
            "comp/ae", "comp/ae", "comp/fu", "comp/mocha", "comp/nuke",
            "comp/render", "comp/render/comp", "comp/render/precomp"
        ]

        for reel in os.listdir(plates_dir):
            reel_path = os.path.join(plates_dir, reel)
            if os.path.isdir(reel_path):
                reel_dir = os.path.join(shots_dir, reel)
                self.ensure_directory_exists(reel_dir)
                for shot in os.listdir(reel_path):
                    shot_path = os.path.join(reel_path, shot)
                    if os.path.isdir(shot_path):
                        shot_name = shot
                    else:
                        shot_name = os.path.splitext(shot)[0]
                    shot_folder = os.path.join(reel_dir, shot_name)
                    if self.ensure_directory_exists(shot_folder):
                        for subfolder in subfolders:
                            self.ensure_directory_exists(os.path.join(shot_folder, subfolder))
            elif os.path.isfile(reel_path):
                default_reel = "seq01"
                reel_dir = os.path.join(shots_dir, default_reel)
                self.ensure_directory_exists(reel_dir)
                shot_name = os.path.splitext(reel)[0]
                shot_folder = os.path.join(reel_dir, shot_name)
                if self.ensure_directory_exists(shot_folder):
                    for subfolder in subfolders:
                        self.ensure_directory_exists(os.path.join(shot_folder, subfolder))
    
        self.projectSelected(self.projects.currentIndex())
    



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





    

    def createTemplateScript(self):
        if not self.projectPath.text():
            QMessageBox.warning(self, "No Project Selected", "Please select a project first.")
            return

        reel_index = self.reels.currentIndex()
        if not reel_index.isValid():
            QMessageBox.warning(self, "No Reel Selected", "Please select a reel first.")
            return

        reel_name = self.reels_model.itemFromIndex(reel_index).text()
        reel_path = os.path.join(self.projectPath.text(), "04_shots", reel_name)

        template_path = os.path.join(reel_path, "_TEMPLATE", "comp", "nuke")
        self.ensure_directory_exists(template_path)

        template_script = os.path.join(template_path, "template_v001.nk")
        if not os.path.exists(template_script):
            nuke.scriptClear()
            nuke.scriptSaveAs(template_script)

        # Refresh shots list so _TEMPLATE appears
        self.reelSelected(reel_index)

        
        # Set Nuke script parameters
        nuke.scriptClear()  # Clear the current Nuke script
        nuke.Root()["first_frame"].setValue(1001)
        nuke.Root()["last_frame"].setValue(1101)
        nuke.Root()["fps"].setValue(23.976)
        nuke.Root()["format"].setValue("UHD_4K")
        
        # Save the template script
        try:
            nuke.scriptSaveAs(template_script)
            self.projectSelected(self.projects.currentIndex()) 
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save template script: {e}")








    def browseProjectFolder(self):
        self.clearSelection()
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.ProjectsPath = QFileDialog.getExistingDirectory(self, "Select Projects Folder", "", options=options)
        if self.ProjectsPath:
            self.ProjectsFolderPath.setText(self.ProjectsPath)
        self.refresh()







    def openFileExplorer(self):
        project_folder = self.projectPath.text()
        if os.path.exists(project_folder):
            if sys.platform == 'darwin':
                subprocess.Popen(['open', project_folder])  # macOS
            elif sys.platform == 'win32':
                subprocess.Popen(['explorer', project_folder])  # Windows
            elif sys.platform == 'linux':
                subprocess.Popen(['xdg-open', project_folder])  # Linux
            else:
                QMessageBox.warning(self, "Unsupported Platform", "Opening file explorer is not supported on this platform.")
        else:
            QMessageBox.warning(self, "Directory Not Found", f"The project directory '{project_folder}' does not exist.")







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

        if self.reels.selectionModel():
            self.reels.selectionModel().currentChanged.connect(self.reelSelected)

    def reelSelected(self, index):
        self.shots_model.clear()
        self.scripts_model.clear()
        self.src.clear()

        reel_item = self.reels_model.itemFromIndex(index)
        if reel_item:
            reel_name = reel_item.text()
            reel_path = os.path.join(self.projectPath.text(), "04_shots", reel_name)
            if os.path.exists(reel_path):
                for shot in os.listdir(reel_path):
                    if os.path.isdir(os.path.join(reel_path, shot)):
                        self.shots_model.appendRow(QStandardItem(shot))

            if self.shots.selectionModel():
                self.shots.selectionModel().currentChanged.connect(self.shotSelected)






    def shotSelected(self, index):
        shot_item = self.shots_model.itemFromIndex(index)
        selected_shot = shot_item.text()
        selected_reel = self.reels.currentIndex().data()
        self.selected_shot_path = os.path.join(self.projectPath.text(), "04_shots", selected_reel, selected_shot)
        self.populateScriptsModel(self.selected_shot_path)
        self.updateSourceTabs(self.projectPath.text(), self.selected_shot_path)







    def scriptSelected(self, index):
        script_item = self.scripts_model.itemFromIndex(index)
        if not script_item:
            return

        project_path = self.projectPath.text()

        # Get selected reel
        reel_index = self.reels.currentIndex()
        if not reel_index.isValid():
            return
        selected_reel = self.reels_model.itemFromIndex(reel_index).text()

        # Get selected shot
        shot_index = self.shots.currentIndex()
        if not shot_index.isValid():
            return
        selected_shot = self.shots_model.itemFromIndex(shot_index).text()

        # Get script name
        selected_script_name = script_item.text()

        # Build full path
        self.selected_script_path = os.path.join(
            project_path, "04_shots", selected_reel, selected_shot, "comp", "nuke", selected_script_name
        )








    def populateScriptsModel(self, selected_shot_path):
        self.scripts_model.clear()
      
        nk_files = []
        for root, dirs, files in os.walk(selected_shot_path):
            for file in files:
                if file.endswith('.nk'):
                    nk_files.append(os.path.join(root, file))
    
        for file_path in nk_files:
            file_name = os.path.basename(file_path)
            item = QStandardItem(file_name)
            self.scripts_model.appendRow(item)







    def updateSourceTabs(self, project_path, selected_shot_path):
        self.src.clear()
        self.addSourceTab(project_path, "01_plates", "plates")

        subdirectories = [d for d in os.listdir(selected_shot_path) if os.path.isdir(os.path.join(selected_shot_path, d))]
        for directory in subdirectories:
            if directory != "comp":  # Exclude the "Comp" directory from tabs
                self.addSourceTab(selected_shot_path, directory, directory)

        self.addSourceTab(os.path.join(selected_shot_path, "comp", "render"), "precomp", "precomp")
        self.addSourceTab(os.path.join(selected_shot_path, "comp", "render"), "comp", "comp")
        self.src.setCurrentIndex(0)







    def addSourceTab(self, path, directory, tab_name):
        tab_page = QWidget()
        tab_layout = QVBoxLayout()
        file_browser = QTreeView()
        file_model = QFileSystemModel()
        file_model.setRootPath(path)
        file_browser.setModel(file_model)
        file_browser.setRootIndex(file_model.index(os.path.join(path, directory)))
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
            comp_path = os.path.join(self.selected_shot_path, "comp", "nuke")
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
            new_script_path = os.path.join(self.selected_shot_path, "comp", "nuke", filename)
            self.ensure_directory_exists(os.path.dirname(new_script_path))

            nuke.scriptClear()
            nuke.scriptSaveAs(new_script_path)

            self.populateScriptsModel(self.selected_shot_path)
            dialog.accept()

        button_box.accepted.connect(accept)
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()






    





    def createNewScript(self, shot_name, task, assignment, version_str, dialog):
        if not shot_name or not task or not assignment or not version_str:
            QMessageBox.warning(self, "Invalid Input", "All fields must be filled.")
            return
    
        try:
            version = int(version_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Version", "Version must be an integer.")
            return
    
        script_dir = os.path.join(self.selected_shot_path, "comp", "nuke")
        if not os.path.exists(script_dir):
            try:
                os.makedirs(script_dir)
            except OSError as e:
                QMessageBox.warning(self, "Directory Creation Failed", f"Failed to create directory '{script_dir}': {e}")
                dialog.reject()
                return
    
        while True:
            script_name = f"{shot_name}_{task}_{assignment}_v{version:03d}.nk"
            script_path = os.path.join(script_dir, script_name)
            if not os.path.exists(script_path):
                break
            version += 1
    
        # Create an empty script file or template
        try:
            with open(script_path, 'w') as f:
                f.write("# New Script Created")
            self.selected_script_path = script_path  # Set the selected script path
            self.populateScriptsModel(self.selected_shot_path)  # Refresh the script list
            self.openScript()  # Open the newly created script
        except IOError as e:
            QMessageBox.warning(self, "Creation Failed", f"Failed to create script: {e}")
        finally:
            dialog.accept()








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
    
        # Optionally, open the new script (adjust this based on your script opening logic)
        self.selected_script_path = new_script_path
        self.openScript()








    def copyNodesFromScript(self):
        if os.path.exists(self.selected_script_path):
            nuke.nodePaste(self.selected_script_path)
        else:
            QMessageBox.warning(self, "Script Not Found", f"The selected script '{self.selected_script_path}' does not exist.")







    def clearSelection(self):
        self.projects_model.clear()
        self.shots_model.clear()
        self.scripts_model.clear()
        self.src.clear()






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
