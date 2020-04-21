import FreeCAD
import FreeCADGui

class BuilderPyWorkbench (FreeCADGui.Workbench):
    "Collection of Builders for FreeCAD Objects"
    
    MenuText = "BuilderPy"
    ToolTip = "Collection of Python Builders"
        # TODO: Add icon self.__class__.Icon = "path/to/icon"        

    def Initialize(self):
        pass

#    def Activated(self):

#   def Deactivated(self):

FreeCADGui.addWorkbench(BuilderPyWorkbench())