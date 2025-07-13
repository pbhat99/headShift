from PySide2 import QtWidgets
import nuke

class TypeSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(TypeSelectionDialog, self).__init__(parent)
        self.setWindowTitle("Select Naming Type")
        self.setMinimumWidth(300)
        
        # Create labels
        self.label1 = QtWidgets.QLabel("SHOT_0000")
        self.label2 = QtWidgets.QLabel("SHOT0000")
        
        # Create buttons
        self.type1_button = QtWidgets.QPushButton("Type 1")
        self.type2_button = QtWidgets.QPushButton("Type 2")
        
        # Create layouts for each button and its label
        button1_layout = QtWidgets.QVBoxLayout()
        button1_layout.addWidget(self.label1)
        button1_layout.addWidget(self.type1_button)
        
        button2_layout = QtWidgets.QVBoxLayout()
        button2_layout.addWidget(self.label2)
        button2_layout.addWidget(self.type2_button)
        
        # Create a horizontal layout for the button columns
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addLayout(button1_layout)
        button_layout.addLayout(button2_layout)
        
        # Set up the main vertical layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # Connect buttons to their respective functions
        self.type1_button.clicked.connect(self.type1_selected)
        self.type2_button.clicked.connect(self.type2_selected)
    
    def type1_selected(self):
        nuke.createNode("kk_write_type01_windows.nk")
        self.accept() 

    def type2_selected(self):
        nuke.createNode("kk_write_type02_windows.nk")
        self.accept() 

# To display the dialog in Nuke
def show_type_selection_dialog():
    # Attempt to find the main window
    main_window = None
    try:
        main_window = next(w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, QtWidgets.QMainWindow))
    except StopIteration:
        pass
    
    dialog = TypeSelectionDialog(parent=main_window)
    dialog.exec_()

# Call this function to display the dialog
#show_type_selection_dialog()
