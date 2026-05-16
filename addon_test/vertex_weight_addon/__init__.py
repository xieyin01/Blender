from .addons.vertex_weight_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": "Vertex Weight Viewer",
    "author": "[Xieyin]",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": "Spine2D-style vertex weight viewer for faceless meshes",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View"
}

def register():
    addon_register()

def unregister():
    addon_unregister()
