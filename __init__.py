'''
scbilliards add-on.
'''

bl_info = {
    "name": "scbilliards",
    "author": "Willard Maier",
    "version": (0, 1),
    "blender": (2, 7, 8),
    "location": "View3D > Add > Mesh > scbilliards",
    "description": "Loads billiard data",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"
}

if "bpy" in locals():
    import importlib
    importlib.reload(loader)
else:
    from . import loader


import bpy


# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator("mesh.scbilliards", text="scbilliards", icon="MESH_DATA")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
