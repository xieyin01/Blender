import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary

# 导入属性组定义
from .properties.properties_group import (
    PCJSDMExportSettings,
    PCJSDMAnimationSettings
)

# Add-on info
bl_info = {
    "name": "Point Cloud JSDM Exporter",
    "author": "諧音",
    "blender": (3, 5, 0),
    "version": (1, 0, 0),
    "description": "导出JSDM格式的点云动画数据，包含动画和颜色导出功能",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "点云导出"
}

# 插件属性声明
_addon_properties = {
    bpy.types.Scene: {
        "pc_jsdm_export_settings": bpy.props.PointerProperty(
            type=PCJSDMExportSettings,
            name="JSDM Export Settings",
            description="JSDM导出设置"
        ),
        "pc_jsdm_animation_settings": bpy.props.PointerProperty(
            type=PCJSDMAnimationSettings,
            name="JSDM Animation Settings",
            description="JSDM动画处理设置"
        )
    }
}


def register():
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    print("{} addon is installed.".format(__addon_name__))


def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)
    
    print("{} addon is uninstalled.".format(__addon_name__))