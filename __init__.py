bl_info = {
    "name": "Screen-Space Hatch Lines",
    "author": "Ane Johanson",
    "version": (0, 2, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Hatch Lines",
    "description": "Create screen-space hatch lines with Grease Pencil v3",
    "warning": "",
    "doc_url": "https://github.com/a-johanson/blender-screen-space-hatch-lines",
    "category": "3D View",
}

import bpy
import importlib
from . import ui, operators

# Support module reloading
if "ui" in locals():
    importlib.reload(ui)
if "operators" in locals():
    importlib.reload(operators)

# Developer reload operator
class HATCH_OT_dev_reload(bpy.types.Operator):
    """Developer tool: Reload addon modules without restarting Blender"""
    bl_idname = "hatch.dev_reload"
    bl_label = "Dev: Reload Addon"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, _context):
        # Reload modules
        importlib.reload(ui)
        importlib.reload(operators)
        
        # Re-register everything
        try:
            unregister()
            register()
            self.report({'INFO'}, "Screen-Space Hatch Lines addon reloaded")
        except Exception as e:
            self.report({'ERROR'}, f"Reload error: {str(e)}")
            register()
            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(HATCH_OT_dev_reload)
    ui.register()
    operators.register()

def unregister():
    operators.unregister()
    ui.unregister()
    try:
        bpy.utils.unregister_class(HATCH_OT_dev_reload)
    except:
        pass

if __name__ == "__main__":
    register()
