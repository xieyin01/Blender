from .addons.vertex_weight_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'Basic Add-on Sample',
    "author": '[You name]',
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": 'This is a template for building addons',
    "warning": '',
    "doc_url": '[documentation url]',
    "tracker_url": '[contact email]',
    "support": 'COMMUNITY',
    "category": '3D View'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    