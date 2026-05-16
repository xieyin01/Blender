from ...common.types.framework import is_extension

# 插件唯一包名，与bl_info中的插件名称不同
__addon_name__ = ".".join(__package__.split(".")[0:3]) if is_extension() else __package__.split(".")[0]

# 插件配置
# 版本信息
VERSION = (1, 0, 0)
VERSION_STRING = ".".join(str(v) for v in VERSION)

# 支持的坐标系
COORDINATE_SYSTEMS = {
    'BLENDER': "Blender (Z-up)",
    'MAYA': "Maya (Y-up)",
}

# 动画模式选项
ANIMATION_MODES = [
    ('NONE', "No Animation", "不导出动画"),
    ('KEYFRAMES', "Keyframes", "导出关键帧动画"),
    ('ALL_FRAMES', "All Frames", "导出所有帧动画")
]

# 颜色模式选项
COLOR_MODES = [
    ('NONE', "No Colors", "不导出颜色"),
    ('VERTEX_COLORS', "Vertex Colors", "导出顶点颜色"),
    ('MATERIAL_COLORS', "Material Colors", "导出材质颜色")
]

# 默认值
DEFAULT_VALUES = {
    'START_FRAME': 1,
    'END_FRAME': 250,
    'FRAME_STEP': 1,
    'SCALE_FACTOR': 1.0,
    'SIMPLIFY_THRESHOLD': 0.001,
    'BATCH_SIZE': 1000
}

# 错误消息
ERROR_MESSAGES = {
    'NO_OBJECT_SELECTED': "未选择对象。请选择网格对象。",
    'INVALID_OBJECT_TYPE': "对象类型无效。请选择网格对象。",
    'EXPORT_FAILED': "导出失败: {}",
    'FILE_NOT_FOUND': "文件未找到: {}",
    'NO_ANIMATION_DATA': "在选中的对象中未找到动画数据。"
}

# 性能设置
PERFORMANCE_SETTINGS = {
    'USE_NUMPY': True,
    'ENABLE_CACHE': True,
    'CACHE_SIZE': 100,
    'MAX_CACHE_MEMORY_MB': 1024
}

# 开发设置
DEVELOPMENT_SETTINGS = {
    'DEBUG_MODE': False,
    'LOG_LEVEL': 'INFO'
}