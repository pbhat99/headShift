import ScriptsManager

ScriptsManager.addScriptsFolderToPluginPath() # Add all folders inside the scripts folder to pluginPath so that they can be accessed
ScriptsManager.createUserDefaultSettings() # Creates default settings if the user has no settings
if os.path.isdir(ScriptsManager.userFolder): # Add the user folder to the plugin path so that the menus are loaded from there (the previous script should have created the folder and settings if they did not exist)
    nuke.pluginAddPath(ScriptsManager.userFolder)
ScriptsManager.createMenu() # Create menus to manage scripts