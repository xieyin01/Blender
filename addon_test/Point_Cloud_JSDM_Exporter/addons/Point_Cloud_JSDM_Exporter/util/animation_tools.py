"""
动画处理工具
提供动画提取、烘焙、优化等功能
"""

import bpy
import math
from typing import Dict, List, Tuple, Optional, Any


class AnimationExtractor:
    """动画提取器"""
    
    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self.mesh = obj.data if obj and obj.type == 'MESH' else None
        self.frames_data = []
        
    def extract_animation_frames(
        self,
        start_frame: int = 1,
        end_frame: int = 250,
        frame_step: int = 1,
        animation_mode: str = 'KEYFRAMES',
        coordinate_system: str = 'BLENDER',
        scale_factor: float = 1.0,
        include_colors: bool = True
    ) -> List[Dict[str, Any]]:
        """提取动画帧数据"""
        if not self.obj or not self.mesh:
            return []
        
        original_frame = bpy.context.scene.frame_current
        
        try:
            frames_data = []
            
            # 根据动画模式确定要提取的帧
            frames_to_extract = self._get_frames_to_extract(
                start_frame, end_frame, frame_step, animation_mode
            )
            
            for i, frame in enumerate(frames_to_extract):
                # 设置当前帧
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()
                
                # 提取帧数据
                frame_data = self._extract_single_frame(
                    frame, coordinate_system, scale_factor, include_colors
                )
                
                if frame_data:
                    frames_data.append(frame_data)
            
            self.frames_data = frames_data
            return frames_data
            
        except Exception as e:
            print(f"提取动画失败: {str(e)}")
            return []
        
        finally:
            # 恢复原始帧
            bpy.context.scene.frame_set(original_frame)
    
    def _get_frames_to_extract(self, start_frame, end_frame, frame_step, animation_mode):
        """获取要提取的帧列表"""
        if animation_mode == 'NONE':
            return [bpy.context.scene.frame_current]
        
        elif animation_mode == 'KEYFRAMES':
            return self._get_keyframes(start_frame, end_frame)
        
        else:  # 'ALL_FRAMES'
            frames = []
            current_frame = start_frame
            
            while current_frame <= end_frame:
                frames.append(current_frame)
                current_frame += frame_step
            
            return frames
    
    def _get_keyframes(self, start_frame, end_frame):
        """获取关键帧"""
        keyframes = set()
        
        if not self.obj.animation_data or not self.obj.animation_data.action:
            return [start_frame]
        
        action = self.obj.animation_data.action
        
        # 获取所有关键帧
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                frame = int(keyframe.co.x)
                if start_frame <= frame <= end_frame:
                    keyframes.add(frame)
        
        if not keyframes:
            keyframes = {start_frame, end_frame}
        
        sorted_keyframes = sorted(list(keyframes))
        
        if start_frame not in sorted_keyframes:
            sorted_keyframes.insert(0, start_frame)
        if end_frame not in sorted_keyframes:
            sorted_keyframes.append(end_frame)
        
        return sorted_keyframes
    
    def _extract_single_frame(self, frame, coordinate_system, scale_factor, include_colors):
        """提取单帧数据"""
        # 计算时间（毫秒）
        fps = bpy.context.scene.render.fps
        time_ms = int((frame - 1) / fps * 1000)
        
        # 获取网格数据（应用修改器）
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = self.obj.evaluated_get(depsgraph)
        
        if not eval_obj or eval_obj.type != 'MESH':
            return None
        
        mesh = eval_obj.data
        n_vertices = len(mesh.vertices)
        
        if n_vertices == 0:
            return None
        
        # 提取位置数据
        positions = []
        world_matrix = eval_obj.matrix_world
        
        for vert in mesh.vertices:
            world_co = world_matrix @ vert.co
            
            # 转换坐标系
            from ..util.coordinate_converter import CoordinateSystemConverter
            converted_co = CoordinateSystemConverter.convert(
                world_co, 'BLENDER', coordinate_system, scale_factor
            )
            positions.append(converted_co)
        
        # 提取ID
        ids = self._extract_ids(mesh)
        
        # 提取颜色
        colors = None
        if include_colors:
            colors = self._extract_colors(mesh)
        
        return {
            "frame": frame,
            "time": time_ms,
            "positions": positions,
            "ids": ids,
            "colors": colors,
            "vertex_count": n_vertices
        }
    
    def _extract_ids(self, mesh):
        """提取ID"""
        n_vertices = len(mesh.vertices)
        
        # 检查ID属性
        if "id" in mesh.attributes:
            attr = mesh.attributes["id"]
            if attr.data_type == 'INT':
                ids = [item.value for item in attr.data]
                
                if len(ids) == n_vertices:
                    # 确保ID从1开始
                    min_id = min(ids)
                    if min_id == 0:
                        ids = [id_val + 1 for id_val in ids]
                    
                    return ids
        
        # 自动生成ID
        return list(range(1, n_vertices + 1))
    
    def _extract_colors(self, mesh):
        """提取颜色"""
        n_vertices = len(mesh.vertices)
        
        if n_vertices == 0:
            return None
        
        # 检查颜色属性
        if "color" in mesh.attributes:
            attr = mesh.attributes["color"]
            if attr.data_type in ['FLOAT_COLOR', 'BYTE_COLOR']:
                colors = []
                from ..util.color_converter import ColorConverter
                
                for item in attr.data:
                    if attr.data_type == 'FLOAT_COLOR':
                        # 浮点颜色 (0-1)
                        r, g, b = item.color[0], item.color[1], item.color[2]
                        colors.append([
                            int(min(max(r, 0), 1) * 255),
                            int(min(max(g, 0), 1) * 255),
                            int(min(max(b, 0), 1) * 255)
                        ])
                    else:  # BYTE_COLOR
                        # 字节颜色 (0-255)
                        r, g, b = item.color[0], item.color[1], item.color[2]
                        colors.append([r, g, b])
                
                if len(colors) == n_vertices:
                    return colors
        
        return None