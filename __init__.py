bl_info = {
    "name": "Screen-Space Shading",
    "author": "Ane Johanson",
    "version": (0, 3, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Screen-Space Shading",
    "description": "Create screen-space shading effects with Grease Pencil v3",
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
