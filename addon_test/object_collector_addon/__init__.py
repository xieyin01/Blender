from .addons.object_collector_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": '物体收藏夹',
    "author": '[Xieyin]',
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": '收藏物体',
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

    