import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary

# 导入属性组定义
from .properties.properties_group import (
    PCJSDMExportSettings
)

#导入操作符
from .operators.export_operator import (
    PCJSDM_OT_Export,
    PCJSDM_OT_InspectGeometryNodes,
)

# 导入面板
from .panels.geometry_nodes_panel import (
    PCJSDM_PT_MainPanel,
    PCJSDM_PT_GeometryNodesPanel,
    PCJSDM_OT_InspectAnimationData,
    menu_func_export
)

# Add-on info
bl_info = {
    "name": "Point Cloud JSDM Exporter",
    "author": "諧音",
    "blender": (3, 5, 0),
    "version": (1, 1, 1),
    "description": "导出几何节点JSDM格式数据，基本实现功能，但是颜色无法输出超过1的值",
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