"""
导出操作符
处理JSDM格式的导出功能
"""

import bpy
import json
import os
import time
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty

from ..config import __addon_name__, ERROR_MESSAGES
from ..util.animation_tools import AnimationExtractor


class PCJSDM_OT_Export(Operator, ExportHelper):
    """导出JSDM格式点云动画"""
    
    bl_idname = "pc_jsdm.export"
    bl_label = "导出JSDM"
    bl_description = "导出JSDM格式点云动画数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 文件选择器属性
    filename_ext = ".jsdm"
    filter_glob: StringProperty(
        default="*.jsdm",
        options={'HIDDEN'}
    )
    
    # 导出设置（可覆盖场景设置）
    use_scene_settings: BoolProperty(
        name="使用场景设置",
        description="使用场景属性中的设置",
        default=True
    )
    
    # 动画设置覆盖
    animation_mode: EnumProperty(
        name="动画模式",
        description="动画导出模式",
        items=[
            ('NONE', "无动画", "不导出动画"),
            ('KEYFRAMES', "关键帧", "导出关键帧动画"),
            ('ALL_FRAMES', "所有帧", "导出所有帧动画")
        ],
        default='KEYFRAMES'
    )
    
    start_frame: IntProperty(
        name="起始帧",
        description="动画起始帧",
        default=1,
        min=1
    )
    
    end_frame: IntProperty(
        name="结束帧",
        description="动画结束帧",
        default=250,
        min=1
    )
    
    frame_step: IntProperty(
        name="帧步长",
        description="帧采样步长",
        default=1,
        min=1
    )
    
    # 数据设置覆盖
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
    
    # 坐标系设置覆盖
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
    
    # 优化设置覆盖
    optimize_animation: BoolProperty(
        name="优化动画",
        description="优化动画数据",
        default=True
    )
    
    def execute(self, context):
        """执行导出操作"""
        # 获取选中的对象
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, ERROR_MESSAGES['NO_OBJECT_SELECTED'])
            return {'CANCELLED'}
        
        if obj.type != 'MESH':
            self.report({'ERROR'}, ERROR_MESSAGES['INVALID_OBJECT_TYPE'])
            return {'CANCELLED'}
        
        try:
            start_time = time.time()
            
            # 获取导出设置
            settings = self._get_export_settings(context)
            
            # 提取动画数据
            extractor = AnimationExtractor(obj)
            frames_data = extractor.extract_animation_frames(
                start_frame=settings['start_frame'],
                end_frame=settings['end_frame'],
                frame_step=settings['frame_step'],
                animation_mode=settings['animation_mode'],
                coordinate_system=settings['coordinate_system'],
                scale_factor=settings['scale_factor'],
                include_colors=settings['include_colors']
            )
            
            if not frames_data:
                self.report({'ERROR'}, ERROR_MESSAGES['NO_ANIMATION_DATA'])
                return {'CANCELLED'}
            
            # 构建JSDM数据结构
            jsdm_data = self._build_jsdm_data(frames_data, settings, obj)
            
            # 保存文件
            export_path = self.filepath
            if not export_path.endswith(self.filename_ext):
                export_path += self.filename_ext
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(jsdm_data, f, indent=2, ensure_ascii=False)
            
            # 报告结果
            elapsed_time = time.time() - start_time
            self.report({'INFO'}, 
                f"成功导出 {len(frames_data)} 帧到 {os.path.basename(export_path)} "
                f"({elapsed_time:.2f}秒)")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, ERROR_MESSAGES['EXPORT_FAILED'].format(str(e)))
            return {'CANCELLED'}
    
    def _get_export_settings(self, context):
        """获取导出设置（优先使用操作符设置，否则使用场景设置）"""
        if not self.use_scene_settings:
            return {
                'animation_mode': self.animation_mode,
                'start_frame': self.start_frame,
                'end_frame': self.end_frame,
                'frame_step': self.frame_step,
                'include_colors': self.include_colors,
                'include_ids': self.include_ids,
                'coordinate_system': self.coordinate_system,
                'scale_factor': self.scale_factor,
                'optimize_animation': self.optimize_animation
            }
        
        # 使用场景设置
        scene_settings = context.scene.pc_jsdm_export_settings
        return {
            'animation_mode': scene_settings.animation_mode,
            'start_frame': scene_settings.start_frame,
            'end_frame': scene_settings.end_frame,
            'frame_step': scene_settings.frame_step,
            'include_colors': scene_settings.include_colors,
            'include_ids': scene_settings.include_ids,
            'coordinate_system': scene_settings.coordinate_system,
            'scale_factor': scene_settings.scale_factor,
            'optimize_animation': scene_settings.optimize_animation
        }
    
    def _build_jsdm_data(self, frames_data, settings, obj):
        """构建JSDM数据结构"""
        # 获取基本信息
        first_frame = frames_data[0] if frames_data else {}
        vertex_count = first_frame.get('vertex_count', 0)
        
        # 构建点帧数据
        point_frames = []
        
        for frame_data in frames_data:
            # 点帧数据（位置和基础颜色）
            point_frame = {
                "time": frame_data.get('time', 0),
                "points": []
            }
            
            positions = frame_data.get('positions', [])
            colors = frame_data.get('colors', [])
            ids = frame_data.get('ids', list(range(1, len(positions) + 1)))
            
            for i, pos in enumerate(positions):
                point = {
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "z": float(pos[2])
                }
                
                # 添加ID
                if settings['include_ids'] and i < len(ids):
                    point["no"] = int(ids[i])
                
                # 添加基础颜色
                if settings['include_colors'] and colors and i < len(colors):
                    color = colors[i]
                    if color:
                        point["c1"] = int(color[0])
                        point["c2"] = int(color[1])
                        point["c3"] = int(color[2])
                
                point_frame["points"].append(point)
            
            point_frames.append(point_frame)
        
        # 构建完整的JSDM数据结构
        jsdm_data = {
            "planeCount": vertex_count,
            "frameCount": len(frames_data),
            "pointFrames": point_frames,
            "metadata": {
                "exportTime": time.strftime("%Y-%m-%d %H:%M:%S"),
                "objectName": obj.name,
                "blenderVersion": bpy.app.version_string,
                "pluginVersion": "1.0.0",
                "settings": {
                    "animationMode": settings['animation_mode'],
                    "coordinateSystem": settings['coordinate_system'],
                    "scaleFactor": settings['scale_factor']
                }
            }
        }
        
        return jsdm_data
    
    def draw(self, context):
        """绘制导出设置面板"""
        layout = self.layout
        
        box = layout.box()
        box.label(text="导出设置", icon='EXPORT')
        
        box.prop(self, "use_scene_settings")
        
        if self.use_scene_settings:
            box.label(text="使用场景中的导出设置", icon='SETTINGS')
        else:
            # 动画设置
            box.label(text="动画设置", icon='ANIM')
            box.prop(self, "animation_mode")
            
            row = box.row(align=True)
            row.prop(self, "start_frame")
            row.prop(self, "end_frame")
            row.prop(self, "frame_step")
            
            # 数据设置
            box.label(text="数据设置", icon='MESH_DATA')
            box.prop(self, "include_colors")
            box.prop(self, "include_ids")
            
            # 坐标系设置
            box.label(text="坐标系", icon='WORLD')
            box.prop(self, "coordinate_system")
            box.prop(self, "scale_factor")