"""
动画处理操作符
处理动画提取、烘焙和优化功能
"""

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, IntProperty, FloatProperty

from ..config import __addon_name__, ERROR_MESSAGES
from ..util.animation_tools import AnimationExtractor


class PCJSDM_OT_ExtractAnimation(Operator):
    """从选中对象提取动画数据"""
    
    bl_idname = "pc_jsdm.extract_animation"
    bl_label = "提取动画"
    bl_description = "从选中对象提取动画数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行动画提取"""
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, ERROR_MESSAGES['NO_OBJECT_SELECTED'])
            return {'CANCELLED'}
        
        if obj.type != 'MESH':
            self.report({'ERROR'}, ERROR_MESSAGES['INVALID_OBJECT_TYPE'])
            return {'CANCELLED'}
        
        try:
            # 获取场景设置
            scene = context.scene
            export_settings = scene.pc_jsdm_export_settings
            anim_settings = scene.pc_jsdm_animation_settings
            
            # 提取动画数据
            extractor = AnimationExtractor(obj)
            frames_data = extractor.extract_animation_frames(
                start_frame=export_settings.start_frame,
                end_frame=export_settings.end_frame,
                frame_step=anim_settings.extract_frame_step,
                animation_mode=anim_settings.extract_animation_mode,
                coordinate_system=export_settings.coordinate_system,
                scale_factor=export_settings.scale_factor,
                include_colors=anim_settings.extract_include_colors
            )
            
            if not frames_data:
                self.report({'WARNING'}, ERROR_MESSAGES['NO_ANIMATION_DATA'])
                return {'CANCELLED'}
            
            # 报告结果
            self.report({'INFO'}, f"提取了 {len(frames_data)} 帧动画数据")
            
            # 打印详细信息
            if export_settings.verbose_logging:
                print(f"\n动画提取详情:")
                print(f"  对象: {obj.name}")
                print(f"  总帧数: {len(frames_data)}")
                print(f"  首帧: {frames_data[0].get('frame', 0)}")
                print(f"  末帧: {frames_data[-1].get('frame', 0)}")
                print(f"  顶点数: {frames_data[0].get('vertex_count', 0)}")
                print(f"  包含颜色: {'colors' in frames_data[0]}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"动画提取失败: {str(e)}")
            return {'CANCELLED'}


class PCJSDM_OT_BakeAnimation(Operator):
    """烘焙动画到关键帧"""
    
    bl_idname = "pc_jsdm.bake_animation"
    bl_label = "烘焙动画"
    bl_description = "烘焙动画到关键帧"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行动画烘焙"""
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, ERROR_MESSAGES['NO_OBJECT_SELECTED'])
            return {'CANCELLED'}
        
        if obj.type != 'MESH':
            self.report({'ERROR'}, ERROR_MESSAGES['INVALID_OBJECT_TYPE'])
            return {'CANCELLED'}
        
        try:
            # 获取场景设置
            scene = context.scene
            anim_settings = scene.pc_jsdm_animation_settings
            export_settings = scene.pc_jsdm_export_settings
            
            original_frame = bpy.context.scene.frame_current
            
            try:
                # 清除现有动画数据
                if obj.animation_data:
                    obj.animation_data_clear()
                
                # 设置关键帧
                keyframe_count = 0
                
                for frame in range(export_settings.start_frame, export_settings.end_frame + 1):
                    bpy.context.scene.frame_set(frame)
                    bpy.context.view_layer.update()
                    
                    if anim_settings.bake_location:
                        obj.keyframe_insert(data_path="location", frame=frame)
                        keyframe_count += 1
                    
                    if anim_settings.bake_rotation:
                        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                        keyframe_count += 1
                    
                    if anim_settings.bake_scale:
                        obj.keyframe_insert(data_path="scale", frame=frame)
                        keyframe_count += 1
                
                # 报告结果
                self.report({'INFO'}, f"成功烘焙 {keyframe_count} 个关键帧")
                
            finally:
                bpy.context.scene.frame_set(original_frame)
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"动画烘焙失败: {str(e)}")
            return {'CANCELLED'}


class PCJSDM_OT_OptimizeAnimation(Operator):
    """优化动画数据"""
    
    bl_idname = "pc_jsdm.optimize_animation"
    bl_label = "优化动画"
    bl_description = "优化动画数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行动画优化"""
        self.report({'INFO'}, "动画优化功能开发中...")
        return {'FINISHED'}