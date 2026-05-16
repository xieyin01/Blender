from .addons.collection_managner_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": '集合管理器',
    "author": 'Xieyin',
    "blender": (3, 5, 0),
    "version": (1, 0, 0),
    "description": '高效的集合标签管理系统',
    "warning": '',
    "doc_url": '',
    "tracker_url": '',
    "support": 'COMMUNITY',
    "category": '3D View'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    