import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary
from JsdmExport_addon.addons.JsdmExport_addon.Inner import register as old_register
from JsdmExport_addon.addons.JsdmExport_addon.Inner import unregister as old_unregister

# Add-on info
bl_info = {
    "name": "无人机表演数据交换 (JSDM)",
    "author": "Your Name", 
    "version": (3, 1, 0),  # 更新到3.1.0版本
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > JSDM Tools",
    "description": "导入导出无人机表演数据，支持序列帧动画，兼容Blender和Maya",
    "category": "Import-Export",
}

_addon_properties = {}


# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# 注意不要在__init__.py文件中自定义PropertyGroup类。请在单独的文件中定义它们并在此处导入。
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

def register():
    old_register()
    # # Register classes
    # auto_load.init()
    # auto_load.register()
    # add_properties(_addon_properties)

    # # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    # print("{} addon is installed.".format(__addon_name__))


def unregister():
    old_unregister()
    # # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # # unRegister classes
    # auto_load.unregister()
    # remove_properties(_addon_properties)
    # print("{} addon is uninstalled.".format(__addon_name__))
