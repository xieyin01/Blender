import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
)


class PCJSDMExportSettings(bpy.types.PropertyGroup):
    """JSDM导出设置属性组"""
    
    # 文件设置
    export_path: StringProperty(
        name="导出路径",
        description="导出文件的保存路径",
        subtype='FILE_PATH',
        default="//export.jsdm"
    )

    # 元数据设置
    project_name: StringProperty(
        name="项目名称",
        description="项目或文件名称",
        default=""
    )
    
    description: StringProperty(
        name="描述",
        description="项目描述",
        default="Exported from Blender Geometry Nodes"
    )
    
    # 数据设置
    include_colors: BoolProperty(
        name="包含颜色",
        description="导出颜色数据",
        default=True
    )
    
    include_ids: BoolProperty(
        name="包含ID",
        description="导出顶点ID",
        default=True
    )

    # 动画设置
    export_animation: BoolProperty(
        name="导出动画",
        description="导出动画序列",
        default=False
    )
    
    frame_start: IntProperty(
        name="起始帧",
        description="动画起始帧",
        default=1,
        min=1,
        max=10000
    )
    
    frame_end: IntProperty(
        name="结束帧",
        description="动画结束帧",
        default=250,
        min=1,
        max=10000
    )
    
    frame_step: IntProperty(
        name="帧步长",
        description="动画帧采样间隔",
        default=1,
        min=1,
        max=100
    )
    
    # 坐标系设置
    coordinate_system: EnumProperty(
        name="坐标系",
        description="导出使用的坐标系",
        items=[
            ('BLENDER', "Blender (Z-up)", "Blender (Z-up)"),
            ('MAYA', "Maya (Y-up)", "Maya (Y-up)"),
        ],
        default='BLENDER'
    )
    
    scale_factor: FloatProperty(
        name="缩放因子",
        description="坐标缩放因子",
        default=1.0,
        min=0.001,
        max=1000.0
    )
    
    # 调试设置
    debug_mode: BoolProperty(
        name="调试模式",
        description="启用调试模式",
        default=False
    )