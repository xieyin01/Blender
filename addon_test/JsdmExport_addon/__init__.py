from .addons.JsdmExport_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": '无人机表演数据交换 (JSDM)',
    "author": 'Your Name',
    "version": (3, 1, 0),
    "blender": (3, 0, 0),
    "location": 'View3D > Sidebar > JSDM Tools',
    "description": '导入导出无人机表演数据，支持序列帧动画，兼容Blender和Maya',
    "category": 'Import-Export'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    