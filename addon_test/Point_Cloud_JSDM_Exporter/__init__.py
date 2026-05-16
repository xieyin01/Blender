from .addons.Point_Cloud_JSDM_Exporter import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'Point Cloud JSDM Exporter',
    "author": '諧音',
    "blender": (3, 5, 0),
    "version": (1, 0, 0),
    "description": '导出JSDM格式的点云动画数据，包含动画和颜色导出功能',
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

    