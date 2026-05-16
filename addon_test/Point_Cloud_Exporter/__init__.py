from .addons.Point_Cloud_Exporter import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'Point Cloud JSDM Exporter',
    "author": '諧音',
    "blender": (3, 5, 0),
    "version": (1, 1, 1),
    "description": '导出几何节点JSDM格式数据，基本实现功能，但是颜色无法输出超过1的值',
    "warning": '',
    "doc_url": '',
    "tracker_url": '',
    "support": 'COMMUNITY',
    "category": '点云导出'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    