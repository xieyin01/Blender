import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
)
from ..config import (
    ANIMATION_MODES,
    COLOR_MODES,
    DEFAULT_VALUES
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
    
    # 动画设置
    animation_mode: EnumProperty(
        name="动画模式",
        description="动画导出模式",
        items=ANIMATION_MODES,
        default='KEYFRAMES'
    )
    
    start_frame: IntProperty(
        name="起始帧",
        description="动画起始帧",
        default=DEFAULT_VALUES['START_FRAME'],
        min=1
    )
    
    end_frame: IntProperty(
        name="结束帧",
        description="动画结束帧",
        default=DEFAULT_VALUES['END_FRAME'],
        min=1
    )
    
    frame_step: IntProperty(
        name="帧步长",
        description="帧采样步长",
        default=DEFAULT_VALUES['FRAME_STEP'],
        min=1
    )
    
    # 数据设置
    include_colors: BoolProperty(
        name="包含颜色",
        description="导出颜色数据",
        default=True
    )
    
    color_mode: EnumProperty(
        name="颜色模式",
        description="颜色导出模式",
        items=COLOR_MODES,
        default='VERTEX_COLORS'
    )
    
    include_ids: BoolProperty(
        name="包含ID",
        description="导出顶点ID",
        default=True
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
        default=DEFAULT_VALUES['SCALE_FACTOR'],
        min=0.001,
        max=1000.0
    )
    
    # 优化设置
    optimize_animation: BoolProperty(
        name="优化动画",
        description="优化动画数据",
        default=True
    )
    
    remove_duplicate_frames: BoolProperty(
        name="移除重复帧",
        description="移除重复的动画帧",
        default=True
    )
    
    simplify_keyframes: BoolProperty(
        name="简化关键帧",
        description="简化关键帧数据",
        default=True
    )
    
    simplify_threshold: FloatProperty(
        name="简化阈值",
        description="关键帧简化阈值",
        default=DEFAULT_VALUES['SIMPLIFY_THRESHOLD'],
        min=0.0,
        max=1.0
    )
    
    # 性能设置
    use_performance_optimizer: BoolProperty(
        name="性能优化",
        description="启用性能优化",
        default=True
    )
    
    batch_size: IntProperty(
        name="批处理大小",
        description="批处理大小",
        default=DEFAULT_VALUES['BATCH_SIZE'],
        min=100,
        max=10000
    )
    
    enable_cache: BoolProperty(
        name="启用缓存",
        description="启用数据缓存",
        default=True
    )
    
    # 调试设置
    debug_mode: BoolProperty(
        name="调试模式",
        description="启用调试模式",
        default=False
    )
    
    verbose_logging: BoolProperty(
        name="详细日志",
        description="启用详细日志记录",
        default=False
    )


class PCJSDMAnimationSettings(bpy.types.PropertyGroup):
    """JSDM动画处理设置属性组"""
    
    # 提取设置
    extract_frame_step: IntProperty(
        name="提取帧步长",
        description="动画提取时的帧步长",
        default=1,
        min=1
    )
    
    extract_animation_mode: EnumProperty(
        name="提取动画模式",
        description="动画提取模式",
        items=ANIMATION_MODES,
        default='KEYFRAMES'
    )
    
    extract_include_colors: BoolProperty(
        name="提取包含颜色",
        description="提取动画时包含颜色",
        default=True
    )
    
    # 烘焙设置
    bake_location: BoolProperty(
        name="烘焙位置",
        description="烘焙位置动画",
        default=True
    )
    
    bake_rotation: BoolProperty(
        name="烘焙旋转",
        description="烘焙旋转动画",
        default=True
    )
    
    bake_scale: BoolProperty(
        name="烘焙缩放",
        description="烘焙缩放动画",
        default=True
    )
    
    bake_simplify_keyframes: BoolProperty(
        name="烘焙简化关键帧",
        description="烘焙时简化关键帧",
        default=True
    )
    
    bake_simplify_threshold: FloatProperty(
        name="烘焙简化阈值",
        description="烘焙关键帧简化阈值",
        default=0.001,
        min=0.0,
        max=1.0
    )
    
    # 优化设置
    optimize_remove_duplicates: BoolProperty(
        name="移除重复",
        description="优化时移除重复帧",
        default=True
    )
    
    optimize_interpolate_missing: BoolProperty(
        name="插值缺失",
        description="优化时插值缺失帧",
        default=False
    )
    
    optimize_max_gap_frames: IntProperty(
        name="最大间隔帧数",
        description="最大插值间隔帧数",
        default=5,
        min=1,
        max=50
    )
    
    # 性能设置
    animation_use_performance_optimizer: BoolProperty(
        name="使用性能优化",
        description="动画处理时使用性能优化",
        default=True
    )
    
    animation_batch_size: IntProperty(
        name="批处理大小",
        description="动画批处理大小",
        default=1000,
        min=100,
        max=10000
    )