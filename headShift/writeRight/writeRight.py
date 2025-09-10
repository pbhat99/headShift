import nuke
import os
import re
from PySide2.QtWidgets import (
    QApplication, # Added for screen geometry
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QWidget, QCheckBox
)
from PySide2.QtCore import Qt

# dont use space,underscore and hifen (" ", "_" "-") which are not supported by nuke node name
FORMAT_PRESETS = [
    {
        "name": "EXRzip",
        "file_type": "exr",
        "subfolder": True,
        "padding": ".%04d",
        "knobs": {
            "compression": "ZIP",
        }
    },
    {
        "name": "EXRdwab",
        "file_type": "exr",
        "subfolder": True,
        "padding": ".%05d",
        "knobs": {
            "autocrop": True,
            "compression": "DWAB",
        }
    },
    {
        "name": "ProRes",
        "file_type": "mov",
        "subfolder": False,
        "padding": "",
        "knobs": {
            "mov64_codec": "appr",
        }
    },
    {
        "name": "h264",
        "file_type": "mov",
        "subfolder": False,
        "padding": "",
        "knobs": {
            "mov64_codec": "h264",
        }
    },
    {
        "name": "JPG",
        "file_type": "jpeg",
        "subfolder": True,
        "padding": ".#####",
        "knobs": {
            "_jpeg_quality": "1"
        }
    }
]

class WriteRightDialog(QDialog):
    def __init__(self, parent=None):
        super(WriteRightDialog, self).__init__(parent)
        self.setWindowTitle("WriteRight - No Node Selected") # Placeholder title
        self.selected_write_node = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Row 1: Node Name, Task, Custom Task, Format, Version, Checkboxes
        row1_layout = QHBoxLayout()

        # Node Name
        self.node_name_edit = QLineEdit()
        self.node_name_edit.setReadOnly(True)
        self.node_name_edit.setStyleSheet("color: yellow; font-weight: bold;")
        row1_layout.addWidget(self.node_name_edit, 2)

        # Task Dropdown
        self.task_label = QLabel("TASK:")
        self.task_combo = QComboBox()
        self.task_combo.addItems(["Comp", "Precomp", "Prep", "Matte", "Denoise", "Retime", "Custom"])
        row1_layout.addWidget(self.task_label)
        row1_layout.addWidget(self.task_combo)

        # Custom Task Input (initially hidden)
        self.custom_task_edit = QLineEdit()
        self.custom_task_edit.setPlaceholderText("Enter custom task name")
        self.custom_task_edit.hide()
        row1_layout.addWidget(self.custom_task_edit, 2)

        # Format Presets Dropdown
        self.format_label = QLabel("PRESET:")
        self.format_combo = QComboBox()
        self.format_combo.addItems([preset["name"] for preset in FORMAT_PRESETS])
        row1_layout.addWidget(self.format_label)
        row1_layout.addWidget(self.format_combo)

        # Version Editable Text
        self.version_label = QLabel("VERSION:")
        self.version_edit = QLineEdit("v001") # Default version
        self.version_edit.setFixedWidth(50)
        row1_layout.addWidget(self.version_label)
        row1_layout.addWidget(self.version_edit)

        # Add separator and checkboxes to the first row
        row1_layout.addSpacing(25) # Padding
        row1_layout.addWidget(QLabel("|")) # Separator
        row1_layout.addSpacing(25) # Padding

        self.seq_name_checkbox = QCheckBox("prefix SEQ Name")
        self.seq_name_checkbox.setChecked(True)
        self.subfolder_checkbox = QCheckBox("Subfolder")
        self.subfolder_checkbox.setChecked(True)

        row1_layout.addWidget(self.seq_name_checkbox)
        row1_layout.addWidget(self.subfolder_checkbox)
        row1_layout.addStretch(1) # Push elements to the left

        main_layout.addLayout(row1_layout)

        # Row 2: Output File Path Preview
        row2_layout = QHBoxLayout()
        # self.path_preview_label = QLabel("Output Path:") # Removed label
        self.path_preview_edit = QLineEdit("C:/path/to/output/file_v001.exr") # Dummy path
        self.path_preview_edit.setReadOnly(True)
        # row2_layout.addWidget(self.path_preview_label) # Removed label
        row2_layout.addWidget(self.path_preview_edit)
        main_layout.addLayout(row2_layout)

        # Row 3: Save and Cancel Buttons
        row3_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        row3_layout.addStretch(1) # Pushes buttons to the right
        row3_layout.addWidget(self.save_button)
        row3_layout.addWidget(self.cancel_button)
        main_layout.addLayout(row3_layout)

        self.setLayout(main_layout)
        # Set initial width to 75% of screen width, and allow scaling
        screen = QApplication.primaryScreen()
        screen_width = screen.geometry().width()
        self.setMinimumWidth(int(screen_width * 0.75))

        # Connect signals to slots
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button.clicked.connect(self.reject) # QDialog's reject closes the dialog

        # Connect UI changes to update path preview
        # self.node_name_edit.textChanged.connect(self.update_path_preview) # Removed this connection
        self.task_combo.currentTextChanged.connect(self.toggle_custom_task_input) # New connection for custom input visibility
        self.task_combo.currentTextChanged.connect(self.update_node_name_from_task)
        self.task_combo.currentTextChanged.connect(self.update_path_preview)
        self.task_combo.currentTextChanged.connect(self.update_displayed_node_name) # New connection for task change
        self.format_combo.currentTextChanged.connect(self.apply_format_preset) # New connection for format preset
        self.format_combo.currentTextChanged.connect(self.update_path_preview)
        self.version_edit.textChanged.connect(self.update_path_preview)
        self.seq_name_checkbox.stateChanged.connect(self.update_path_preview)
        self.subfolder_checkbox.stateChanged.connect(self.update_path_preview)
        self.custom_task_edit.textChanged.connect(self.update_path_preview) # New connection for custom input changes
        self.custom_task_edit.textChanged.connect(self.update_node_name_from_task) # New connection for custom input changes
        self.custom_task_edit.textChanged.connect(self.update_displayed_node_name) # New connection for custom input changes

    def set_write_node(self, node):
        self.selected_write_node = node
        if self.selected_write_node:
            self.setWindowTitle(f"WriteRight - {self.selected_write_node.name()}") # Keep original title for now
            # self.original_node_name is no longer stored here
            # self.node_name_edit.setText(self.original_node_name) is handled by update_displayed_node_name

            # Attempt to parse existing path for initial values
            self.parse_path_for_initial_values(self.selected_write_node['file'].value())
            self.version_edit.setText(self.get_nuke_script_version()) # Autopopulate version
            
            # Connect format combo to update displayed node name
            self.format_combo.currentTextChanged.connect(self.update_displayed_node_name)
            self.update_displayed_node_name() # Call once to set initial displayed name
            self.update_path_preview()
        else:
            self.setWindowTitle("WriteRight - No Node Selected")
            self.node_name_edit.clear()
            self.path_preview_edit.clear()

    def parse_path_for_initial_values(self, path):
        # This is a simplified parser. A robust one would handle more cases.
        # Example path: /path/to/project/shot_name/comp/render_v001.exr
        basename = os.path.basename(path)
        name, ext = os.path.splitext(basename)

        # Try to extract version
        version_match = re.search(r'_v(\d+)', name)
        if version_match:
            self.version_edit.setText(f"v{int(version_match.group(1)):03d}")
            name_without_version = name[:version_match.start()]
        else:
            name_without_version = name

        # Set format
        if ext:
            self.format_combo.setCurrentText(ext[1:].upper()) # Remove dot and make uppercase


        # Try to parse task and format from node name
        node_name = self.selected_write_node.name()
        # Regex to match "Write_TASK_FORMAT"
        match = re.match(r"Write_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)", node_name)
        if match:
            task_from_name = match.group(1)
            format_from_name = match.group(2)

            # Set task combo
            index = self.task_combo.findText(task_from_name, Qt.MatchContains)
            if index != -1:
                self.task_combo.setCurrentIndex(index)
            else:
                # If not in predefined tasks, set to Custom and populate custom_task_edit
                self.task_combo.setCurrentText("Custom")
                self.custom_task_edit.setText(task_from_name)

            # Set format combo based on format_from_name
            # Need to find the preset name that matches the format_from_name (e.g., "EXR_zip" for "EXR_zip")
            found_preset_for_name = False
            for preset in FORMAT_PRESETS:
                if preset["name"].lower() == format_from_name.lower():
                    self.format_combo.setCurrentText(preset["name"])
                    found_preset_for_name = True
                    break
            if not found_preset_for_name:
                # If format from name doesn't match a preset name, try matching file_type
                for preset in FORMAT_PRESETS:
                    if preset["file_type"].lower() == format_from_name.lower():
                        self.format_combo.setCurrentText(preset["name"])
                        found_preset_for_name = True
                        break

        

    def apply_format_preset(self, preset_name):
        if not self.selected_write_node:
            return

        selected_preset = None
        for preset in FORMAT_PRESETS:
            if preset["name"] == preset_name:
                selected_preset = preset
                break

        if selected_preset:
            # Set subfolder checkbox state
            self.subfolder_checkbox.setChecked(selected_preset["subfolder"])

            # Update displayed node name and path preview
            self.update_displayed_node_name()
            self.update_path_preview()


    def update_displayed_node_name(self):
        # Get current task
        task = self.task_combo.currentText()
        if task == "Custom":
            task = self.custom_task_edit.text()
        
        # Get current format
        current_format = self.format_combo.currentText()

        # Construct displayed name as Write_taskname_formatname
        displayed_name = f"Write_{task}_{current_format}"
        self.node_name_edit.setText(displayed_name)


    def toggle_custom_task_input(self, text):
        if text == "Custom":
            self.custom_task_edit.show()
        else:
            self.custom_task_edit.hide()

    def update_node_name_from_task(self):
        task = self.task_combo.currentText()
        if task == "Custom":
            task = self.custom_task_edit.text() # Use custom input
        # No longer setting node_name_edit directly from here
        # The displayed node name is handled by update_displayed_node_name
        pass

    def get_nuke_script_version(self):
        script_path = nuke.root().name()
        if script_path:
            basename = os.path.basename(script_path)
            name, ext = os.path.splitext(basename)
            version_match = re.search(r'[._-]v(\d+)', name, re.IGNORECASE) # More flexible regex
            if version_match:
                version_num = int(version_match.group(1))
                return f"v{version_num:03d}"
        return "v001" # Default if no version found or script not saved

    def update_path_preview(self):
        task = self.task_combo.currentText()
        if task == "Custom":
            task = self.custom_task_edit.text() # Use custom input
        task = task.lower() # Keep original case for task in path
        version = self.version_edit.text()

        # Get the selected format preset
        selected_preset_name = self.format_combo.currentText()
        selected_preset = None
        for preset in FORMAT_PRESETS:
            if preset["name"] == selected_preset_name:
                selected_preset = preset
                break

        if not selected_preset:
            # Fallback if preset not found (shouldn't happen if combo box is populated correctly)
            file_extension = "exr" # Default to exr
        else:
            file_extension = selected_preset["file_type"]

        # The base node name for path generation should be 'Write_taskname_formatname'
        # This is consistent with the displayed node name.
        base_node_name_for_path = f"Write_{task}_{selected_preset_name.upper()}" # Use task and format for path node name
        node_name = base_node_name_for_path # This is the 'node_name' for the path

        # Get checkbox states
        use_seq_name_in_filename = self.seq_name_checkbox.isChecked()
        use_subfolder = self.subfolder_checkbox.isChecked()

        script_path = nuke.root().name()
        if not script_path:
            self.path_preview_edit.setText("Nuke script not saved. Cannot generate path.")
            return

        # Normalize path for consistent splitting
        script_path = script_path.replace("\\", "/")

        # Split the path into components
        path_parts = script_path.split('/')

        # Find the 'nuke' directory to determine the shot path
        try:
            nuke_dir_index = path_parts.index('nuke')
            # The shot path is everything up to 'nuke'
            shot_path_parts = path_parts[:nuke_dir_index]
            shot_path = '/'.join(shot_path_parts)

            project_name = shot_path_parts[-2] if len(shot_path_parts) >= 2 else "unknown_project"
            

            shot_name = shot_path_parts[-1] if len(shot_path_parts) >= 1 else "unknown_shot"

        except ValueError:
            self.path_preview_edit.setText("Could not parse script path for project/shot structure.")
            return
        except IndexError:
            self.path_preview_edit.setText("Could not determine project/shot name from script path.")
            return

        # Construct the RENDER directory path
        render_base_dir = os.path.join(shot_path, "RENDER").replace("\\", "/")
        
        version_clean = version.lstrip('vV')
        if not version_clean.isdigit():
            version_clean = "001" # Fallback if version is not numeric
        formatted_version = f"v{int(version_clean):03d}"

        # Construct the base file name (without padding and extension)
        file_name_parts_for_base = []
        if use_seq_name_in_filename:
            file_name_parts_for_base.append(project_name)
        file_name_parts_for_base.extend([shot_name, task, formatted_version])
        base_file_name = '_'.join(file_name_parts_for_base)

        # Apply subfolder logic
        render_dir = render_base_dir
        if use_subfolder:
            render_dir = os.path.join(render_base_dir, base_file_name).replace("\\", "/")

        # Always include frame padding
        file_name = f"{base_file_name}{selected_preset['padding']}.{file_extension}"
        
        full_output_path = os.path.join(render_dir, file_name).replace("\\", "/")
        
        self.path_preview_edit.setText(full_output_path)


    def save_changes(self):
        if not self.selected_write_node:
            QMessageBox.warning(self, "No Node Selected", "Please select a Write node in Nuke.")
            return

        # Get the selected format preset
        selected_preset_name = self.format_combo.currentText()
        selected_preset = None
        for preset in FORMAT_PRESETS:
            if preset["name"] == selected_preset_name:
                selected_preset = preset
                break

        if not selected_preset:
            QMessageBox.critical(self, "Error", "Selected format preset not found.")
            return

        # Get the displayed node name (Write_taskname_formatname)
        new_node_name_display = self.node_name_edit.text()
        new_file_path = self.path_preview_edit.text()

        try:
            # Set the file type on the Write node
            self.selected_write_node['file_type'].setValue(selected_preset["file_type"])

            # Update file path
            self.selected_write_node['file'].setValue(new_file_path)

            # Apply knobs from selected preset
            for knob_name, knob_value in selected_preset["knobs"].items():
                try:
                    # Special handling for mov64_write_codec for Nuke 13+
                    if knob_name == "mov64_write_codec":
                        self.selected_write_node["codec"].setValue(knob_value)
                    else:
                        self.selected_write_node[knob_name].setValue(knob_value)
                except Exception as e:
                    print(f"Warning: Could not set knob '{knob_name}' on Write node: {e}")

            # Update node name
            self.selected_write_node.setName(new_node_name_display)

            # Update node name
            self.selected_write_node.setName(new_node_name_display)

            self.accept() # Close dialog on success
        except:
            print ('cant update node name')

def show_write_right_dialog():
    selected_nodes = nuke.selectedNodes()
    write_nodes = [node for node in selected_nodes if node.Class() == 'Write']
    
    target_node = None

    if not write_nodes:
        print("No Write node selected. Creating a new Write node.")
        target_node = nuke.createNode('Write')
    else:
        # Write node(s) selected
        if len(write_nodes) > 1:
            print("Multiple Write nodes selected. Using the first one found.")
        target_node = write_nodes[0]
    
    if target_node:
        dialog = WriteRightDialog()
        dialog.set_write_node(target_node)
        dialog.exec_() # Show as modal dialog