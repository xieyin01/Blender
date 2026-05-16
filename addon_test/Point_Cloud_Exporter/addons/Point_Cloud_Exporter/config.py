from ...common.types.framework import is_extension

# 插件唯一包名
__addon_name__ = ".".join(__package__.split(".")[0:3]) if is_extension() else __package__.split(".")[0]

# 错误消息
ERROR_MESSAGES = {
    'NO_OBJECT_SELECTED': "未选择对象。请选择对象。",
    'NO_GEOMETRY_NODES': "对象没有几何节点修改器。",
    'EXPORT_FAILED': "导出失败: {}",
}