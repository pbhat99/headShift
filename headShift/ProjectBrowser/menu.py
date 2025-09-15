import nuke

# Add Project Browser based on Nuke version
if nuke.NUKE_VERSION_MAJOR == 12: 
    import ProjectBrowser_27
    nuke.menu('Nuke').addCommand('Pipeline/Project Browser', 'ProjectBrowser_27.custom_ui.show()', "shift+B")
    from ProjectBrowser_27 import ProjectBrowser
else:
    import ProjectBrowser_36
    nuke.menu('Nuke').addCommand('Pipeline/Project Browser', 'ProjectBrowser_36.custom_ui.show()', "shift+B") 
    from ProjectBrowser_36 import ProjectBrowser


if sys.platform == 'win32':
    from WriteTypeSelector_windows import show_type_selection_dialog
elif sys.platform == 'linux':
    from WriteTypeSelector_linux import show_type_selection_dialog

nuke.menu('Nuke').addCommand('Pipeline/Write Selector', 'show_type_selection_dialog()', 'shift+w')


nuke.menu('Nuke').addCommand('Pipeline/Write Manager', 'import WriteManager; WriteManager.show_write_manager_dialog()', icon='Write.png')
