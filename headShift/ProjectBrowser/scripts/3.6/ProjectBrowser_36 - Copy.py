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
        self.setWindowTitle('Project Browser v1.0 - Kostiantyn Kokariev')

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
        self.lay_grd_main.addLayout(self.lay_buttonVert, 1, 3, 1, 1)

    def createWidgets(self):
        self.label = QLabel("Projects Directory:")
        self.label1 = QLabel("Projects")
        self.label2 = QLabel("Shots")
        self.label3 = QLabel("Scripts")

        self.ProjectsFolderPath = QLineEdit()
        self.ProjectsFolderPath.setReadOnly(True)
        self.projectPath = QLineEdit()

        self.projects = QListView()
        self.projects_model = QStandardItemModel()
        self.projects.setModel(self.projects_model)
        self.projects.setFixedWidth(200)

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
        self.lay_grd_project.addWidget(self.label, 0, 0, 1, 1)
        self.lay_grd_project.addWidget(self.ProjectsFolderPath, 0, 1, 1, 1)
        self.lay_grd_project.addWidget(self.browseButton, 0, 2, 1, 1)
        self.lay_grd_project.addWidget(self.newProjectButton, 1, 0, 1, 1)
        self.lay_grd_project.addWidget(self.shotsButton, 2, 0, 1, 1)
        self.lay_grd_project.addWidget(self.refreshButton, 1, 2, 1, 1)
        self.lay_grd_project.addWidget(self.explButton, 2, 2, 1, 1)
        self.lay_grd_project.addWidget(self.templateButton, 3, 0, 1, 1)

        self.lay_grd_main.addWidget(self.label1, 0, 0, 1, 1)
        self.lay_grd_main.addWidget(self.label2, 0, 1, 1, 1)
        self.lay_grd_main.addWidget(self.label3, 0, 2, 1, 1)
        self.lay_grd_main.addWidget(self.projects, 1, 0, 1, 1)
        self.lay_grd_main.addWidget(self.shots, 1, 1, 1, 1)
        self.lay_grd_main.addWidget(self.scripts, 1, 2, 1, 1)

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
    
        # Create shot folders and subfolders
        for item in os.listdir(plates_dir):
            item_path = os.path.join(plates_dir, item)
            if os.path.isdir(item_path) or os.path.isfile(item_path):
                shot_name = os.path.splitext(item)[0]
                shot_folder = os.path.join(shots_dir, shot_name)
                if self.ensure_directory_exists(shot_folder):
                    for subfolder in subfolders:
                        self.ensure_directory_exists(os.path.join(shot_folder, subfolder))
    
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
        project_path = self.projectPath.text()
        if not project_path:
            QMessageBox.warning(self, "No Project Selected", "Please select a project first.")
            return
        
        # Define the template directory path
        template_dir = os.path.join(project_path, "04_shots", "template", "comp", "nuke")
        
        # Ensure the directory exists
        if not os.path.exists(template_dir):
            try:
                os.makedirs(template_dir)
            except OSError as e:
                QMessageBox.warning(self, "Directory Creation Failed", f"Failed to create directory '{template_dir}': {e}")
                return
        
        # Define the template script path
        template_script_path = os.path.join(template_dir, "template.nk")
        
        # Set Nuke script parameters
        nuke.scriptClear()  # Clear the current Nuke script
        nuke.Root()["first_frame"].setValue(1001)
        nuke.Root()["last_frame"].setValue(1101)
        nuke.Root()["fps"].setValue(23.976)
        nuke.Root()["format"].setValue("UHD_4K")
        
        # Save the template script
        try:
            nuke.scriptSaveAs(template_script_path)
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
            subdirectories = [d for d in os.listdir(self.ProjectsPath) if os.path.isdir(os.path.join(self.ProjectsPath, d))]
            for directory in subdirectories:
                item = QStandardItem(directory)
                self.projects_model.appendRow(item)
            self.projects.setModel(self.projects_model)
            self.projects.selectionModel().currentChanged.connect(self.projectSelected)
        else:
            QMessageBox.warning(self, "Directory Not Found", f"The projects directory '{self.ProjectsPath}' does not exist.")







    def projectSelected(self, index):
        self.shots_model.clear()
        self.scripts_model.clear()
        self.src.clear()
        # Temporarily disconnect to avoid triggering shotSelected incorrectly
        try:
            self.shots.selectionModel().currentChanged.disconnect()
        except TypeError:
            # Handle case where selectionModel or currentChanged is None or already disconnected
            pass
    
        if index.isValid():

            selected_folder = os.path.join(self.ProjectsPath, self.projects_model.itemFromIndex(index).text())
            if selected_folder:
                self.projectPath.setText(selected_folder)
                shots_folder = os.path.join(selected_folder, "04_shots")
                if os.path.exists(shots_folder) and os.path.isdir(shots_folder):
                    subdirectories = [d for d in os.listdir(shots_folder) if os.path.isdir(os.path.join(shots_folder, d))]
                    for directory in subdirectories:
                        item = QStandardItem(directory)
                        self.shots_model.appendRow(item)    
        # Reconnect the signal after updating
        if self.shots.selectionModel():
            self.shots.selectionModel().currentChanged.connect(self.shotSelected)







    def shotSelected(self, index):
        shot_item = self.shots_model.itemFromIndex(index)
        selected_shot = shot_item.text()
        self.selected_shot_path = os.path.join(self.projectPath.text(), "04_shots", selected_shot)
        self.populateScriptsModel(self.selected_shot_path)
        self.updateSourceTabs(self.projectPath.text(), self.selected_shot_path)







    def scriptSelected(self, index):
        # Get the name of the selected script
        selected_script_name = index.data()
        # Construct the full path to the selected script
        project_path = self.projectPath.text()
        selected_shot = self.shots.currentIndex().data()
        selected_script_path = os.path.join(project_path, "04_shots", selected_shot, "comp", "nuke", selected_script_name)

        if os.path.exists(selected_script_path):
            self.selected_script_path = selected_script_path  # Store the selected script path
        else:
            self.selected_script_path = ""
            QMessageBox.warning(self, "Script Not Found", f"The script '{selected_script_name}' does not exist.")







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
    
        # Create the dialog for input
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Script")
    
        main_layout = QVBoxLayout()
    
        # Horizontal layout for shot label and name
        shot_layout = QHBoxLayout()
        shot_label = QLabel("Shot Name:")
        shot_name = QLabel(os.path.basename(self.selected_shot_path))
        shot_layout.addWidget(shot_label)
        shot_layout.addWidget(shot_name)
        main_layout.addLayout(shot_layout)
    
        # Horizontal layout for task, assignment, and version
        input_layout = QHBoxLayout()
    
        task_label = QLabel("Task:")
        task_input = QLineEdit()
        input_layout.addWidget(task_label)
        input_layout.addWidget(task_input)
    
        assignment_label = QLabel("Assignment:")
        assignment_input = QLineEdit()
        input_layout.addWidget(assignment_label)
        input_layout.addWidget(assignment_input)
    
        version_label = QLabel("Version:")
        version_input = QLineEdit()
        version_input.setMaxLength(3)
        version_input.setText("001")
        input_layout.addWidget(version_label)
        input_layout.addWidget(version_input)
    
        main_layout.addLayout(input_layout)
    
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(button_box)
    
        dialog.setLayout(main_layout)
    
        # Connect the buttons
        button_box.accepted.connect(lambda: self.createNewScript(shot_name.text(), task_input.text(), assignment_input.text(), version_input.text(), dialog))
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
        print(f"Attempting to open script: {self.selected_script_path}")
        if os.path.exists(self.selected_script_path):
            nuke.scriptOpen(self.selected_script_path)
        else:
            QMessageBox.warning(self, "Script Not Found", f"The selected script '{self.selected_script_path}' does not exist.")







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
