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

from . import ui, operators

def register():
    ui.register()
    operators.register()

def unregister():
    operators.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()
