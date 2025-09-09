import nuke, nukescripts
import os, json, getpass, re

curDir = os.path.dirname(__file__).replace("\\", "/") # Current directory
infoFile = f"{curDir}/scripts_info.json" # Required information about scripts, filled in edit_script_info
scriptsDir = f"{os.path.dirname(curDir)}/scripts" # Folder where all scripts are located
userFolder = f"{curDir}/users/{getpass.getuser()}" # From this folder, menus are loaded for the user, each user has their own folder
userDataFile = f"{userFolder}/data.json" # Information about enabled/disabled user scripts
userMenuFile = f"{userFolder}/menu.py" # File that will create menus for the user
scripts_manager_users = ["asus", "Asus"] # Users for whom a menu is created for editing scripts for adding and deleting information about them

def get_scripts(addToPluginPath=False):
    """
    Returns a dictionary with all found scripts.

    The dictionary key is the script name (without the .py extension),
    and the value is the path where the script will be located in the Nuke menu.
    If addToPluginPath is True, then each folder containing scripts,
    will be added to Nuke's pluginPath. This is useful if new scripts
    were added while Nuke was running and their folders were not yet in the pluginPath.
    """
    scripts = {}
    for fileDir, _, files in os.walk(scriptsDir):
        for file in files:
            if file.endswith(".py"):
                menu_path = fileDir[len(scriptsDir)+1:].replace("\\", "/") # And the path to the folder, we discard the path to the scripts folder to get the path in the menu
                script_name = os.path.splitext(file)[0] # Discard .py
                scripts[script_name] = menu_path
        if addToPluginPath:
            nuke.pluginAddPath(fileDir.replace("\\", "/"))
    return scripts

def writeAndAddMenu(file, info, createMenus=False):
    """
    Writes a menu to a file and creates a menu in Nuke
    Args:
        file: The file to which the menu will be written
        info: Script information
        createMenus: Flag indicating whether to create a menu in Nuke. If False then only write data to a file, by default False because it is used more often in scripts where menu creation is not required
    """
    if info["custom_cmd_checkbox"]: # Let's see what we will use to create the menu, using regular parameters or through a custom menu
        file.write(info["custom_command"] + "\n") # Write a custom command
        if createMenus: # Execute the code immediately if necessary
            exec(info["custom_command"]) # TODO might be worth doing in try except because you might have messed up the command
    else:
        menu_path, command, icon, shortcut, context, index = [info[n] for n in ["menu_path", "command", "icon", "shortcut", "shortcut_context", "index"]] # We do not check, we assume that the necessary parameters are in the database
        if context in ["0", "1", "2"]: # If you need to specify a specific context
            file.write(f"nuke.menu('Nuke').addCommand('{menu_path}', '{command}', '{shortcut}', icon='{icon}', index={index}, shortcutContext={context})\n")
            if createMenus:
                nuke.menu("Nuke").addCommand(menu_path, command, shortcut, icon=icon, index=index, shortcutContext=int(context))
        else:
            file.write(f"nuke.menu('Nuke').addCommand('{menu_path}', '{command}', '{shortcut}', icon='{icon}', index={index})\n")
            if createMenus:
                nuke.menu("Nuke").addCommand(menu_path, command, shortcut, icon=icon, index=index)

class ScriptsManagerPanel(nukescripts.PythonPanel):
    """Class for the window for enabling/disabling scripts by the user"""
    def __init__(self, scripts, info, userData):
        nukescripts.PythonPanel.__init__(self, "Scripts Manager")
        self.filter = nuke.String_Knob("filter", "")
        self.addKnob(self.filter)
        self.addKnob(nuke.PyScript_Knob("filter_button", "filter"))
        self.scripts_knobs = [] # Knobs responsible for scripts
        for scr in scripts: # Go through each script in alphabetical order
            if info.get(scr): # If there is information about the script
                menu_path = info[scr]["menu_path"]
                kn = nuke.Boolean_Knob(scr, menu_path.split("/")[-1]) # Create a knob for it
                kn.setFlag(nuke.STARTLINE)
                if userData and userData.get(scr)!=None: # If there is already recorded data for the user, substitute it
                    kn.setValue(userData[scr])
                kn.setTooltip(f"{info[scr]['tooltip']}\n<i>{menu_path}</i>") # Set a hint about what the script does
                self.addKnob(kn)
                self.scripts_knobs.append(kn) # Add the knob to the list of knobs that need to be processed later
    
    def knobChanged(self, kn):
        if kn.name()=="filter_button":
            filter = self.filter.value().lower()
            for kn in self.scripts_knobs:
                if kn.name().lower().count(filter) or kn.label().lower().count(filter) or kn.tooltip().lower().count(filter):
                    kn.setVisible(True)
                else:
                    kn.setVisible(False)

def removeMenu(info: dict):
    """Removes the menu when disabling the script in scripts_manager"""
    menu_paths = []
    if info["custom_cmd_checkbox"]:
        for line in info["custom_command"].split("\n"): # Commands are split into lines
            if line.count(".addCommand(")==1:
                menu_path = line.split(".addCommand(")[1].split(",")[0].strip("'").strip('"')
                menu_paths.append(menu_path)
    else:
        menu_paths.append(info["menu_path"])
    for menu_path in menu_paths:
        spl = menu_path.split("/") # Full path
        menu = "/".join(spl[:-1]) # Path to the menu where the script button is located
        m = nuke.menu("Nuke").menu(menu)
        if not m: # If we didn't find such a menu, we'll just look in the Nuke menu
            m = nuke.menu("Nuke")
        if m.findItem(spl[-1]): # If we found the button, delete it
            m.removeItem(spl[-1])
        baseMenu = nuke.menu("Nuke").findItem(spl[0]) # Base menu folder(Udmurtia, File)
        if not isinstance(baseMenu,nuke.Menu): # If there are no scripts left in the menu, it becomes a MenuItem and then it should be deleted
            nuke.menu("Nuke").removeItem(spl[0])

def scripts_manager():
    """Main menu for enabling/disabling plugins"""
    if not os.path.isfile(infoFile): # Check if scripts_info.json exists, it is impossible to work without it
        nuke.message("Need scripts_info.json file")
        return
    info, userData = [None, None]
    with open(infoFile, "r", encoding="utf-8") as file: # Read data from info file
        info = json.load(file)
    if not info: # Check if we were able to read something from info
        nuke.message("Error reading file scripts_info.json")
        return
    if os.path.isfile(userDataFile): # If there is a file for the user, we also read the data
        with open(userDataFile, "r", encoding="utf-8") as file:
            userData = json.load(file)
    scripts = get_scripts(True) # Get all available scripts in alphabetical order
    if not scripts:
        nuke.message("Didn't find any scripts in the scripts folder")
        return
    panel = ScriptsManagerPanel(scripts, info, userData) # Launch the panel
    if not panel.showModalDialog(): # If the cancel button was pressed, exit the script
        return
    if not os.path.isdir(userFolder): # If there is no folder for the user, create it
        os.makedirs(userFolder)
    data = {}
    file = open(userMenuFile, "w", encoding="utf-8")
    for kn in panel.scripts_knobs:
        scr = kn.name()
        data[scr] = kn.value() # Record whether the user enabled or disabled the script
        if kn.value():
            writeAndAddMenu(file, info[scr], True)
        else:
            removeMenu(info[scr])
    file.close()
    with open(userDataFile, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    nuke.message("Scripts successfully modified!\n(Nuke may need to be restarted)")

class EditScriptPanel(nukescripts.PythonPanel):
    """Class for the window with editing information about scripts"""
    def __init__(self, scripts: dict, info: dict):
        """
        Args:
            scripts (dict): Dictionary with the script name and the path to the menu where it should be located
            info (dict): Information about scripts: command, hotkey, etc.
        """
        nukescripts.PythonPanel.__init__(self, "Edit Script")
        self.setMinimumSize(550, 350) # Enlarge the window
        self.scripts = scripts # Write to local variables for further access to them
        self.info = info
        context_list = ["No context", "0", "1", "2"] # List of parameters for the shortcut_context knob
        # Default values for knobs, the script name is passed to lambda s
        self.defaults = {"default": False,
                         "menu_name": lambda s: re.sub(r"([A-Z])", r" \1", s).strip().title(),
                         "command": lambda s: f"import {s}; {s}.{s}()",
                         "custom_command": "",
                         "custom_cmd_checkbox": False,
                         "tooltip": "",
                         "icon": "",
                         "shortcut": "",
                         "shortcut_context": context_list[0],
                         "index": -1,
                         "menu_path": lambda s: f"{self.scripts[s]}/{self.knobs()['menu_name'].value()}"}
        # Description of all necessary knobs
        self.script = nuke.Enumeration_Knob("script", "Скрипт", list(scripts.keys()))
        self.script.setTooltip("The script we want to add or change. The list is formed from all files with the .py extension in the scriptsDir folder.")
        self.default = nuke.Boolean_Knob("default", "Enabled by default")
        self.default.setTooltip("If the user has no settings for this script, it will be automatically set to True. Also, when loading the nuke, if the user has no settings at all, this script will be immediately added to the user")
        self.default.setFlag(nuke.STARTLINE)
        self.custom_cmd_checkbox = nuke.Boolean_Knob("custom_cmd_checkbox", "Кастомная команда")
        self.custom_cmd_checkbox.setTooltip("Enables the mode in which you need to enter the command that will be executed when the program starts and create a menu or assign callbacks")
        self.menu_name = nuke.String_Knob("menu_name", "Menu name")
        self.menu_name.setTooltip("The name that will be displayed in the menu for calling the script")
        self.command = nuke.String_Knob("command", "Command")
        self.command.setTooltip("The command that will be executed when the script call button is pressed")
        self.custom_command = nuke.Multiline_Eval_String_Knob("custom_command", "Команда")
        self.custom_command.setTooltip("A command that will be written in the user's menu.py file and will be executed when the program is launched. It can both create a menu of any number and with any behavior independent of the parameters of this menu, and, for example, set callbacks.")
        self.tooltip = nuke.Multiline_Eval_String_Knob("tooltip", "Описание")
        self.tooltip.setTooltip("Script description that will be shown when hovering the mouse over the script in the Script Manager menu")
        self.icon = nuke.String_Knob("icon", "Иконка")
        self.icon.setTooltip("Icon for the script menu. You need to write it with an extension, for example <b>icon.png</b> The extension is not controlled in any way, whatever is written in this field will be substituted. Therefore, you need to make sure that the extension is specified.")
        self.shortcut = nuke.String_Knob("shortcut", "Hot key")
        self.shortcut.setTooltip("Hotkey for calling the script")
        self.shortcut_context = nuke.Enumeration_Knob("shortcut_context", "Контекст", context_list)
        self.shortcut_context.setTooltip("Hotkey call context:\n<b>0</b> Window\n<b>1</b> Application\n<b>2</b> DAG\nYou need to select 2 when you want the hotkey to work only in the nodegraph and not in the viewer.\nIn this case, you may need to designate hotkeys with:\n<b>^</b> Ctrl\n<b>#</b> Alt\n<b>+</b> Shift")
        self.index = nuke.Int_Knob("index", "Position(index)")
        self.index.setTooltip("The position where the script call button will be located in the menu. For example, you can add a script to the File menu in the second position. The value -1 means that the script will be added to the end of the menu")
        self.menu_path = nuke.Text_Knob("menu_path", "Menu path")
        self.menu_path.setTooltip("Path to script in menu")
        self.my_knobs = [self.script, self.default, self.custom_cmd_checkbox, self.menu_name, self.command, self.custom_command, self.tooltip, self.icon, self.shortcut, self.shortcut_context, self.index, self.menu_path]  # Порядок добавления кнобов в меню
        for kn in self.my_knobs:
            self.addKnob(kn)
        self.my_knobs.insert(1, self.my_knobs.pop(3)) # Move menu_name to the second position to ignore this knob later like script
        self.setupKnobValues() # Set the value for the knobs
    
    def knobChanged(self, kn):
        if kn.name()=="script":
            self.setupKnobValues()
        elif kn.name()=="menu_name": # When we change the name of the script in the menu, we take the path to the menu from self.scripts
            self.menu_path.setValue(f"{self.scripts[self.script.value()]}/{self.menu_name.value()}")
        elif kn.name()=="command":
            kn.setValue(kn.value().replace("'",'"')) # Replace single quotes with double ones, this is important for writeAndAddMenu because single quotes are used there
        elif kn.name()=="custom_cmd_checkbox":
            self.disableKnobsIfCustomCommand()
    
    def setFromDefaults(self, kn, scr):
        """Sets the value of the knob kn from the dictionary self.defaults"""
        default = self.defaults.get(kn.name())
        if callable(default):
            kn.setValue(default(scr))
        elif default!=None:
            kn.setValue(default)
    
    def disableKnobsIfCustomCommand(self):
        """Enables/disables certain buttons if custom_cmd_checkbox is checked"""
        enable = self.custom_cmd_checkbox.value()
        for kn in ["menu_name", "command", "icon", "shortcut", "shortcut_context", "index", "menu_path"]:
            self.knobs()[kn].setVisible(not enable)
        self.knobs()["custom_command"].setVisible(enable)

    def setupKnobValues(self):
        """Sets the values for knobs from the scripts_info.json file, if not, then the default"""
        scr = self.script.value() # The currently selected script for which you want to set the settings
        info = self.info.get(scr) # Information for the current script
        if info: # If there is already an entry for the script in scripts_info.json, set it
            for kn in self.my_knobs[2:-1]: # Everything except the script name (it is already installed), menu_name (it is not in info, it is taken from menu_path) and menu_path (it is taken from self.scripts)
                if info.get(kn.name())!=None: # Check that such a knob is in info (in case we added a new knob that wasn't there before)
                    kn.setValue(info[kn.name()])
                else:
                    self.setFromDefaults(kn,scr) # If parameter could not be found in info, set default value
            self.menu_name.setValue(info["menu_path"].split("/")[-1]) # Set menu_name from menu_path
            self.menu_path.setValue(f"{self.scripts[scr]}/{self.menu_name.value()}") # Then set menu_path from scripts (in case we moved the script to a new location)
        else: # Default values for knobs
            for kn in self.my_knobs[1:]: # For each knob we look for the default value
                self.setFromDefaults(kn, scr)
        self.disableKnobsIfCustomCommand()

def edit_script_info():
    """Adds/modifies script information in the scripts_info.json file."""
    scripts = get_scripts() # Get all available scripts in alphabetical order
    if not scripts:
        nuke.message("Didn't find any scripts in the scripts folder")
        return
    if not os.path.isfile(infoFile): # Create scripts_info.json file if it doesn't exist
        with open(infoFile, "w", encoding="utf-8") as file:
            json.dump({}, file, indent=4, ensure_ascii=False)
    with open(infoFile, "r", encoding="utf-8") as file: # Read data from info file
        info = json.load(file)
    p = EditScriptPanel(scripts, info)
    if p.showModalDialog(): # If the user clicked OK
        info[p.my_knobs[0].value()] = {kn.name(): kn.value() for kn in p.my_knobs[2:]} # we don't write menu_name because it is contained in menu_path
        with open(infoFile, "w", encoding="utf-8") as file: # Write data to file
            json.dump(info, file, indent=4, ensure_ascii=False)
        updateUsersMenu()

def remove_script_info():
    """
    Removes the script entry in the scripts_info.json file.
    In this case, this script will not be deleted from users, but it will no longer appear.
    in the Scripts Manager selection list. Just when the user goes to configure
    your scripts, they will be updated and the script will disappear.
    """
    if not os.path.isfile(infoFile):
        nuke.message("Need scripts_info.json file")
        return
    with open(infoFile, "r", encoding="utf-8") as file: # Read data from info file
        info = json.load(file)
    p = nuke.Panel("Remove Script")
    p.setWidth(226)
    for script in info:
        p.addBooleanCheckBox(script, False)
    if p.show():
        for script in list(info.keys()): # list(info.keys()) helps prevent RuntimeError: dictionary changed size during iteration because it returns a copy of the list
            if p.value(script):
                info.pop(script) # We can use pop since we are looping through a copy of the list using list(info.keys())
        with open(infoFile, "w", encoding="utf-8") as file:
            json.dump(info, file, indent=4, ensure_ascii=False)
        updateUsersMenu() # Update the settings for users to remove the scripts that were just deleted

def createUserDefaultSettings(userDataFile=userDataFile, userMenuFile=userMenuFile):
    """
    On boot, Nuke creates default settings for the user if they don't already have them.
    This is necessary so that the user already has the necessary scripts when loading for the first time,
    such as ReadFromWrite and Reveal in Folder. By default, the function is executed
    for the current user, but you can pass `userDataFile` and `userMenuFile`
    for a custom user (used in `updateUsersMenu`).
    """
    # If the settings exist, you don't need to do anything. If there is not at least one file, we will create one and overwrite the other.
    if os.path.isfile(userDataFile) and os.path.isfile(userMenuFile):
        return
    scripts = get_scripts() # Get all available scripts in alphabetical order
    if not scripts: # If there are no scripts, exit the function
        return
    if not os.path.isfile(infoFile): # Check if scripts_info.json exists, it stores information about default scripts
        return
    with open(infoFile, "r", encoding="utf-8") as file: # Read data from info file
        info = json.load(file)
    if not os.path.isdir(userFolder): # If there is no folder for the user, create it
        os.makedirs(userFolder)
    data = {}
    file = open(userMenuFile, "w", encoding="utf-8") # Write default menus for the user
    for scr in scripts: # Go through all the scripts
        if info.get(scr) is None: # Check that there is information for the script
            continue
        data[scr] = info[scr]["default"] # Write whether the plugin is enabled or disabled
        if info[scr]["default"]: # If this is a default script, it needs to be added to the menu.py file
            writeAndAddMenu(file, info[scr]) # We don't create the menu right away, because we create the menu.py file and the menu will be created automatically from the file
    file.close()
    with open(userDataFile, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def updateUsersMenu():
    """
    For all users in the users folder, recreate menu.py.
    Creation occurs based on the included scripts in userDataFile and the new
    information from scripts_info.json that the user does not yet have.
    If the user does not have a data.json or menu.py file, they will be created
    using `createUserDefaultSettings`. This function is called in `edit_script_info`
    after changing the script info and in `remove_script_info` to
    update remote scripts.
    """
    scripts = get_scripts() # Get all available scripts in alphabetical order
    if not scripts: # If there are no scripts, exit the function
        return
    if not os.path.isfile(infoFile): # Check if scripts_info.json exists
        return
    with open(infoFile, "r", encoding="utf-8") as file: # Read data from info file
        info = json.load(file)
    users_dir = f"{curDir}/users"
    if not os.path.isdir(users_dir): # Need to check that the users folder exists before the next os.listdir operation
        return
    for user in os.listdir(users_dir): # Loop through folders and files in the folder with all users
        user_folder = f"{users_dir}/{user}"
        if os.path.isdir(user_folder): # Check that this is a folder and not a file
            user_data_file = f"{user_folder}/data.json"
            user_menu_file = f"{user_folder}/menu.py"
            if os.path.isfile(user_data_file) and os.path.isfile(user_menu_file): # Check that both settings files exist
                with open(user_data_file, "r", encoding="utf-8") as file:
                    userData = json.load(file) # Information about enabled/disabled scripts, we will eventually add new information to it or remove what is no longer relevant
                data = {} # New data that we will write to userDataFile
                file = open(user_menu_file, "w", encoding="utf-8")
                for scr in scripts: # Go through all the scripts
                    if info.get(scr) is None: # Check that there is information for the script (if not, this script will not be added to the user's menu.py, even if it was there before).
                        continue
                    # We need to understand whether we are adding a script to the menu or not, this can be understood through the already existing userData or, if there is no entry in it, look in default.
                    enable = userData.get(scr)
                    if enable is None:
                        enable = info[scr]["default"]
                    data[scr] = enable
                    if enable:
                        writeAndAddMenu(file, info[scr]) # We do not create a menu because we write menu.py not for the current user, the menu will be created for the user when the nuke is launched.
                file.close()
                with open(user_data_file, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
            else:
                createUserDefaultSettings(user_data_file, user_menu_file) # Create settings files from scratch, adding only default scripts
                # This function repeats the functionality just performed by the current function, for example getting scripts scripts = get_scripts() and checking for the existence of the required files.
                # But since this code is not executed when the script is loaded, we can ignore the optimization and execution speed of this script.
    nuke.message("Successfully updated!")

def addScriptsFolderToPluginPath():
    """
    Adds all folders inside the scripts folder to the pluginPath for access.
    TODO: We need to make exceptions, for example for the __pycache__ folders.
    """
    for root, _, _ in os.walk(scriptsDir): # If the folder does not exist, there will be no error, the loop will simply not start
        if root != "__pycache__":
            nuke.pluginAddPath(root.replace("\\", "/"))

def createMenu():
    """
    Creates a menu for managing scripts.
    For regular users, it's just a matter of turning scripts on and off.
    For selected users from the `scripts_manager_users` list there is also a menu
    to manage script information and delete script information.
    """
    if getpass.getuser() in scripts_manager_users:
        nuke.menu("Nuke").addCommand("Edit/Scripts Manager/Scripts Manager", "ScriptsManager.scripts_manager()") # Allows you to enable and disable scripts
        nuke.menu("Nuke").addCommand("Edit/Scripts Manager/Edit Scripts Info", "ScriptsManager.edit_script_info()") # Add/edit script info
        nuke.menu("Nuke").addCommand("Edit/Scripts Manager/Remove Script", "ScriptsManager.remove_script_info()") # Removing scripts
        nuke.menu("Nuke").addCommand("Edit/Scripts Manager/Update Users Menus", "ScriptsManager.updateUsersMenu()") # Updates settings for all users
    else:
        nuke.menu("Nuke").addCommand("Edit/Scripts Manager", "ScriptsManager.scripts_manager()") # Allows you to enable and disable scripts

def setScriptStateForAllUsers(name: str, state: bool):
    """Useful when you need to change whether a plugin is enabled or disabled for all users at once"""
    users_dir = f"{curDir}/users"
    if not os.path.isdir(users_dir): # Need to check that the users folder exists before the next os.listdir operation
        return
    for user in os.listdir(users_dir): # Loop through folders and files in the folder with all users
        user_folder = f"{users_dir}/{user}"
        if os.path.isdir(user_folder): # Check that this is a folder and not a file
            user_data_file = f"{user_folder}/data.json"
            if os.path.isfile(user_data_file): # Check that there is a settings file
                with open(user_data_file, "r", encoding="utf-8") as file:
                    userData = json.load(file)
                if name in userData:
                    userData[name] = state
                    with open(user_data_file, "w", encoding="utf-8") as file:
                        json.dump(userData, file, indent=4, ensure_ascii=False)