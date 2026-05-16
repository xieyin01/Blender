bl_info = {
    "name": "无人机表演数据交换 (JSDM)",
    "author": "Your Name", 
    "version": (3, 3, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > JSDM Tools",
    "description": "导入导出无人机表演数据，支持序列帧动画，兼容Blender和Maya",
    "category": "Import-Export",
}

import bpy
import bmesh
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (StringProperty, IntProperty, CollectionProperty, 
                      FloatProperty, BoolProperty, EnumProperty)
import json
import os
from datetime import datetime
import time
import re

# ==================== 辅助类定义 ====================

class FileEncodingDetector:
    @staticmethod
    def read_json_file(file_path):
        """安全读取JSON文件，自动处理编码"""
        encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                if content.startswith('\ufeff'):
                    content = content[1:]
                
                data = json.loads(content)
                print(f"成功使用编码: {encoding}")
                return data
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue
        
        # 最终尝试：二进制读取
        try:
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
            
            # 尝试常见编码
            for encoding in ['utf-8', 'gbk', 'latin-1']:
                try:
                    content = content_bytes.decode(encoding, errors='ignore')
                    content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
                    data = json.loads(content)
                    print(f"最终使用编码（忽略错误）: {encoding}")
                    return data
                except:
                    continue
        except Exception as e:
            raise Exception(f"无法读取文件: {e}")

class JSDM_Progress:
    def __init__(self, context, total_steps, message):
        self.context = context
        self.total_steps = total_steps
        self.current_step = 0
        self.message = message
        self.start_time = time.time()
        
        if hasattr(context, 'window_manager'):
            wm = context.window_manager
            wm.progress_begin(0, 100)
    
    def update(self, step_message=""):
        self.current_step += 1
        progress = self.current_step / self.total_steps
        
        elapsed_time = time.time() - self.start_time
        if progress > 0:
            estimated_total = elapsed_time / progress
            remaining_time = estimated_total - elapsed_time
            time_str = f"预计剩余: {remaining_time:.1f}秒"
        else:
            time_str = "计算中..."
        
        if hasattr(self.context, 'window_manager'):
            wm = self.context.window_manager
            wm.progress_update(progress * 100)
        
        print(f"{self.message}: {int(progress*100)}% {step_message} {time_str}")
        return True
    
    def finish(self):
        if hasattr(self.context, 'window_manager'):
            wm = self.context.window_manager
            wm.progress_end()

class CoordinateSystemConverter:
    @staticmethod
    def convert_coordinates(location, source_system, target_system):
        """坐标转换 - 确保Maya和Blender之间正确转换"""
        if source_system == target_system:
            return location
        
        x, y, z = location
        
        if source_system == 'BLENDER' and target_system == 'MAYA':
            # Blender (Z-up, Y-forward) -> Maya (Y-up, Z-forward)
            # X保持不变，Y和Z交换
            return (x, z, y)
        
        elif source_system == 'MAYA' and target_system == 'BLENDER':
            # Maya (Y-up, Z-forward) -> Blender (Z-up, Y-forward)
            # X保持不变，Y和Z交换
            return (x, z, y)
        
        return (x, y, z)

# ==================== 属性类定义 ====================

class JSDMExportProperties(PropertyGroup):
    # 基础设置
    drone_size: FloatProperty(
        name="无人机尺寸",
        description="导入时无人机的默认尺寸",
        default=0.5,
        min=0.1,
        max=5.0
    )
    
    emission_strength: FloatProperty(
        name="自发光强度",
        description="无人机材质的自发光强度",
        default=10.0,
        min=0.0,
        max=50.0
    )
    
    subdivision_level: IntProperty(
        name="细分等级",
        description="无人机球体的细分等级（1=低质量，3=高质量）",
        default=2,
        min=1,
        max=4
    )
    
    # 导入设置
    import_animation: BoolProperty(
        name="导入动画",
        description="导入序列帧动画数据",
        default=True
    )
    
    import_colors: BoolProperty(
        name="导入颜色",
        description="导入颜色动画数据",
        default=True
    )
    
    import_compatibility_mode: EnumProperty(
        name="导入兼容模式",
        description="选择导入文件的来源软件",
        items=[
            ('BLENDER', "Blender (Z-up)", "导入Blender导出的文件"),
            ('MAYA', "Maya (Y-up)", "导入Maya导出的文件"),
        ],
        default='BLENDER'
    )
    
    # 导出设置
    export_mode: EnumProperty(
        name="导出模式",
        description="选择导出数据源",
        items=[
            ('OBJECTS', "选中无人机", "将选中的网格物体作为无人机"),
            ('VERTICES', "网格顶点", "将选中物体的顶点作为无人机位置"),
        ],
        default='OBJECTS'
    )
    
    export_animation: BoolProperty(
        name="导出动画",
        description="导出动画序列而非单帧",
        default=False
    )
    
    start_frame: IntProperty(
        name="开始帧",
        description="动画开始帧",
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
        description="采样帧间隔",
        default=1,
        min=1,
        max=10
    )
    
    export_colors: BoolProperty(
        name="导出颜色",
        description="导出无人机颜色数据",
        default=True
    )
    
    export_compatibility_mode: EnumProperty(
        name="导出兼容模式",
        description="选择导出文件的兼容软件",
        items=[
            ('BLENDER', "Blender (Z-up)", "导出为Blender兼容格式"),
            ('MAYA', "Maya (Y-up)", "导出为Maya兼容格式"),
        ],
        default='BLENDER'
    )
    
    # 场景设置
    scene_fps: IntProperty(
        name="场景帧率",
        description="设置场景帧率（帧/秒）- 影响动画速度",
        default=10,
        min=1,
        max=120
    )
    
    # 性能设置
    batch_size: IntProperty(
        name="批处理大小",
        description="每批创建的无人机数量（小值=内存友好，大值=处理快速）",
        default=1000,
        min=100,
        max=5000
    )
    
    show_progress: BoolProperty(
        name="显示进度条",
        description="在右下角显示操作进度",
        default=True
    )
    
    # UI设置
    show_export_settings: BoolProperty(
        name="显示导出设置",
        description="显示详细的导出设置选项",
        default=False
    )

# ==================== 动画导入器 ====================

class JSDMAnimationImporter:
    def __init__(self, context, jsdm_tool):
        self.context = context
        self.jsdm_tool = jsdm_tool
        self.drone_materials = {}
    
    def import_animation(self, data, collection):
        """导入动画数据 - 支持Maya和Blender格式"""
        point_frames = data.get('pointFrames', [])
        channel_frames = data.get('channelFrames', [])
        
        if not point_frames:
            return []
        
        # 使用用户选择的兼容模式
        compatibility_mode = self.jsdm_tool.import_compatibility_mode
        
        # 创建无人机
        drones = self.create_drones_from_frame(point_frames[0], collection, compatibility_mode)
        
        if self.jsdm_tool.import_animation:
            self.setup_position_animation(drones, point_frames, compatibility_mode)
            
            if self.jsdm_tool.import_colors and channel_frames:
                self.setup_color_animation(drones, channel_frames)
        
        return drones
    
    def create_drones_from_frame(self, frame_data, collection, compatibility_mode):
        """从第一帧数据创建无人机"""
        points = frame_data.get('points', [])
        drones = []
        
        for i, point in enumerate(points, 1):
            x, y, z = point.get('x', 0), point.get('y', 0), point.get('z', 0)
            
            # 根据兼容模式转换坐标
            if compatibility_mode == 'MAYA':
                # Maya坐标转Blender坐标
                location = CoordinateSystemConverter.convert_coordinates((x, y, z), 'MAYA', 'BLENDER')
            else:
                # Blender坐标保持原样
                location = (x, y, z)
            
            drone = self.create_drone(location, i)
            collection.objects.link(drone)
            
            self.setup_drone_material(drone, i)
            
            # 设置初始颜色（如果有）
            if point.get('c1') is not None:
                color = self.normalize_color(
                    point.get('c1', 255),
                    point.get('c2', 255),
                    point.get('c3', 255)
                )
                self.set_drone_color(drone, color, 1)
            
            drones.append(drone)
        
        return drones
    
    def setup_position_animation(self, drones, point_frames, compatibility_mode):
        """设置位置动画"""
        fps = self.jsdm_tool.scene_fps
        
        for frame_data in point_frames:
            time_value = frame_data.get('time', 0)  # 毫秒
            frame_number = int((time_value / 1000.0) * fps) + 1
            
            self.context.scene.frame_set(frame_number)
            
            points = frame_data.get('points', [])
            for i, drone in enumerate(drones):
                if i < len(points):
                    point = points[i]
                    x, y, z = point.get('x', 0), point.get('y', 0), point.get('z', 0)
                    
                    # 根据兼容模式转换坐标
                    if compatibility_mode == 'MAYA':
                        location = CoordinateSystemConverter.convert_coordinates((x, y, z), 'MAYA', 'BLENDER')
                    else:
                        location = (x, y, z)
                    
                    drone.location = location
                    drone.keyframe_insert(data_path="location", frame=frame_number)
        
        # 设置时间轴范围
        if point_frames:
            max_time = max([f.get('time', 0) for f in point_frames])
            max_frame = int((max_time / 1000.0) * fps) + 1
            self.context.scene.frame_end = max_frame
    
    def setup_color_animation(self, drones, channel_frames):
        """设置颜色动画"""
        fps = self.jsdm_tool.scene_fps
        
        for frame_data in channel_frames:
            time_value = frame_data.get('time', 0)  # 毫秒
            frame_number = int((time_value / 1000.0) * fps) + 1
            
            self.context.scene.frame_set(frame_number)
            
            channels = frame_data.get('channels', [])
            for channel in channels:
                drone_no = channel.get('no', 0)
                if 1 <= drone_no <= len(drones):
                    drone = drones[drone_no - 1]
                    color = self.normalize_color(
                        channel.get('c1', 255),
                        channel.get('c2', 255),
                        channel.get('c3', 255)
                    )
                    self.set_drone_color(drone, color, frame_number)
    
    def create_drone(self, location, index):
        """创建无人机对象"""
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=self.jsdm_tool.subdivision_level,
            radius=0.5 * self.jsdm_tool.drone_size,
            location=location
        )
        drone = self.context.active_object
        drone.name = f"drone_{index:06d}"
        
        return drone
    
    def setup_drone_material(self, drone, index):
        """设置无人机材质"""
        mat = bpy.data.materials.new(name=f"drone_{index:06d}_mat")
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = (1, 1, 1, 1)
        emission.inputs['Strength'].default_value = self.jsdm_tool.emission_strength
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        
        mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        if drone.data.materials:
            drone.data.materials[0] = mat
        else:
            drone.data.materials.append(mat)
        
        self.drone_materials[index] = {
            'material': mat,
            'emission_node': emission
        }
    
    def set_drone_color(self, drone, color, frame_number):
        """设置无人机颜色"""
        if not drone.data.materials:
            return
        
        mat = drone.data.materials[0]
        if not mat.use_nodes:
            return
        
        for node in mat.node_tree.nodes:
            if node.type == 'EMISSION':
                node.inputs['Color'].default_value = color
                node.inputs['Color'].keyframe_insert(
                    data_path="default_value",
                    frame=frame_number
                )
                break
    
    def normalize_color(self, r, g, b):
        """将0-255的颜色值转换为0-1"""
        return (
            max(0, min(1, r / 255.0)),
            max(0, min(1, g / 255.0)),
            max(0, min(1, b / 255.0)),
            1.0
        )

# ==================== 导入操作符 ====================

class IMPORT_OT_jsdm(Operator):
    bl_idname = "import_scene.jsdm"
    bl_label = "导入JSDM"
    bl_description = "导入无人机表演数据，支持序列帧动画，兼容Maya和Blender格式"
    
    filename_ext = ".jsdm"
    filter_glob: StringProperty(default="*.jsdm", options={'HIDDEN'})
    filepath: StringProperty(name="文件路径", maxlen=1024, default="")

    def execute(self, context):
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        try:
            # 读取文件
            print(f"开始读取文件: {self.filepath}")
            data = FileEncodingDetector.read_json_file(self.filepath)
            
            if not self.validate_jsdm_data(data):
                self.report({'ERROR'}, "无效的JSDM文件格式")
                return {'CANCELLED'}
            
            # 获取帧数据
            point_frames = data.get("pointFrames", [])
            channel_frames = data.get("channelFrames", [])
            
            # 检查动画数据
            has_animation = len(point_frames) > 1
            
            if has_animation and not jsdm_tool.import_animation:
                self.report({'INFO'}, f"检测到 {len(point_frames)} 帧动画数据，但未启用动画导入")
            
            # 创建或获取集合
            collection_name = "Imported_Drones"
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
            else:
                collection = bpy.data.collections.new(collection_name)
                scene.collection.children.link(collection)
            
            # 设置场景FPS
            if jsdm_tool.import_animation and has_animation:
                scene.render.fps = jsdm_tool.scene_fps
                scene.render.fps_base = 1.0
            
            # 导入数据
            importer = JSDMAnimationImporter(context, jsdm_tool)
            created_drones = importer.import_animation(data, collection)
            
            if not created_drones:
                self.report({'ERROR'}, "没有成功创建任何无人机")
                return {'CANCELLED'}
            
            # 选择所有创建的无人机
            bpy.ops.object.select_all(action='DESELECT')
            for drone in created_drones:
                drone.select_set(True)
            
            drone_count = len(created_drones)
            
            # 设置视图
            if created_drones:
                context.view_layer.objects.active = created_drones[0]
                bpy.ops.view3d.view_selected()
                bpy.ops.view3d.view_all()
            
            # 报告结果
            if has_animation and jsdm_tool.import_animation:
                position_frames = len(point_frames)
                color_frames = len(channel_frames) if channel_frames else 0
                animation_info = f"，位置{position_frames}帧"
                if color_frames > 0:
                    animation_info += f"，颜色{color_frames}帧"
                
                # 设置时间轴范围
                scene.frame_start = 1
                if point_frames:
                    max_time = max([f.get('time', 0) for f in point_frames])
                    fps = jsdm_tool.scene_fps
                    max_frame = int((max_time / 1000.0) * fps) + 1
                    scene.frame_end = max_frame
                
                self.report({'INFO'}, f"成功导入 {drone_count} 架无人机{animation_info}")
            else:
                self.report({'INFO'}, f"成功导入 {drone_count} 架无人机")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"导入失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def validate_jsdm_data(self, data):
        """验证JSDM数据格式"""
        if 'planeCount' not in data:
            print("缺少planeCount字段")
            return False
        
        if 'pointFrames' not in data:
            print("缺少pointFrames字段")
            return False
        
        point_frames = data.get('pointFrames', [])
        if not point_frames:
            print("没有点帧数据")
            return False
        
        first_frame = point_frames[0]
        if 'points' not in first_frame or not first_frame['points']:
            print("第一帧没有点数据")
            return False
        
        return True
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ==================== 导出操作符 ====================

class EXPORT_OT_jsdm(Operator):
    bl_idname = "export_scene.jsdm"
    bl_label = "导出JSDM"
    bl_description = "导出无人机表演数据为JSDM格式，兼容Maya和Blender"
    
    filename_ext = ".jsdm"
    filter_glob: StringProperty(default="*.jsdm", options={'HIDDEN'})
    filepath: StringProperty(name="文件路径", maxlen=1024, default="")
    description: StringProperty(name="描述", default="")
    
    def execute(self, context):
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        if jsdm_tool.export_animation:
            if jsdm_tool.start_frame > jsdm_tool.end_frame:
                self.report({'ERROR'}, "开始帧不能大于结束帧")
                return {'CANCELLED'}
        
        start_time = time.time()
        
        try:
            if jsdm_tool.export_animation:
                json_data = self.build_jsdm_animation_data(context, jsdm_tool)
            else:
                json_data = self.build_jsdm_static_data(context, jsdm_tool)
            
            if not json_data:
                self.report({'ERROR'}, "没有找到有效的无人机数据")
                return {'CANCELLED'}
            
            file_path = self.filepath.replace('\\', '/')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            end_time = time.time()
            frame_count = json_data.get("frameCount", 1)
            drone_count = json_data.get("planeCount", 0)
            
            if jsdm_tool.export_animation:
                point_frames = json_data.get("pointFrames", [])
                channel_frames = json_data.get("channelFrames", [])
                position_frames = len(point_frames)
                color_frames = len(channel_frames) if channel_frames else 0
                frame_info = f"（位置{position_frames}帧"
                if color_frames > 0:
                    frame_info += f"，颜色{color_frames}帧"
                frame_info += "）"
            else:
                frame_info = ""
            
            self.report({'INFO'}, f"成功导出 {drone_count} 架无人机 {frame_count} 帧数据{frame_info}，耗时 {end_time-start_time:.1f}秒")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def build_jsdm_static_data(self, context, jsdm_tool):
        """构建静态数据"""
        drones_data = self.get_drones_data(context, jsdm_tool)
        if not drones_data:
            return None
        
        return self.build_json_structure(drones_data, jsdm_tool, False)
    
    def build_jsdm_animation_data(self, context, jsdm_tool):
        """构建动画数据"""
        original_frame = context.scene.frame_current
        
        # 获取第一帧数据
        context.scene.frame_set(jsdm_tool.start_frame)
        context.view_layer.update()
        first_frame_data = self.get_drones_data(context, jsdm_tool)
        
        if not first_frame_data:
            context.scene.frame_set(original_frame)
            return None
        
        plane_count = len(first_frame_data)
        point_frames = []
        channel_frames = []
        
        total_frames = (jsdm_tool.end_frame - jsdm_tool.start_frame) // jsdm_tool.frame_step + 1
        
        print(f"导出设置: 共{total_frames}帧，帧步长{jsdm_tool.frame_step}")
        
        # 进度条
        progress = None
        if jsdm_tool.show_progress:
            progress = JSDM_Progress(context, total_frames, "导出动画帧")
        
        frame_index = 0
        for frame in range(jsdm_tool.start_frame, jsdm_tool.end_frame + 1, jsdm_tool.frame_step):
            context.scene.frame_set(frame)
            context.view_layer.update()
            
            if progress and not progress.update(f"帧 {frame}"):
                context.scene.frame_set(original_frame)
                return None
            
            drones_data = self.get_drones_data(context, jsdm_tool)
            
            if len(drones_data) != plane_count:
                print(f"警告: 帧 {frame} 无人机数量不一致，跳过")
                continue
            
            # 计算时间（毫秒）
            time_val = (frame - jsdm_tool.start_frame) / context.scene.render.fps * 1000
            
            # 构建位置帧
            point_frame = self.build_point_frame(drones_data, time_val, jsdm_tool)
            if point_frame and point_frame['points']:
                point_frames.append(point_frame)
            
            # 构建颜色帧
            if jsdm_tool.export_colors:
                channel_frame = self.build_channel_frame(drones_data, time_val)
                if channel_frame and channel_frame['channels']:
                    channel_frames.append(channel_frame)
            
            frame_index += 1
        
        if progress:
            progress.finish()
        
        context.scene.frame_set(original_frame)
        
        actual_frame_count = len(point_frames)
        if actual_frame_count == 0:
            return None
        
        return self.build_json_structure(
            first_frame_data, jsdm_tool, True, 
            actual_frame_count, point_frames, channel_frames
        )
    
    def build_point_frame(self, drones_data, time_val, jsdm_tool):
        """构建位置帧数据 - 按照您提供的文件格式"""
        point_frame = {
            "time": int(round(time_val)),  # 整数毫秒
            "points": []
        }
        
        compatibility_mode = jsdm_tool.export_compatibility_mode
        
        for i, drone_data in enumerate(drones_data, 1):
            if 'location' not in drone_data:
                continue
                
            location = drone_data['location']
            
            # 坐标转换
            if compatibility_mode == 'MAYA':
                # Blender转Maya
                converted_location = CoordinateSystemConverter.convert_coordinates(
                    location, 'BLENDER', 'MAYA'
                )
            else:
                # 保持Blender坐标
                converted_location = location
            
            point_data = {
                "x": round(converted_location[0], 3),
                "y": round(converted_location[1], 3),
                "z": round(converted_location[2], 3),
                "no": i
            }
            
            # 注意：这里不包含颜色数据，颜色数据在独立的channelFrames中
            point_frame["points"].append(point_data)
        
        return point_frame
    
    def build_channel_frame(self, drones_data, time_val):
        """构建颜色帧数据 - 按照您提供的文件格式"""
        channel_frame = {
            "time": int(round(time_val)),  # 整数毫秒
            "channels": []
        }
        
        for i, drone_data in enumerate(drones_data, 1):
            if 'color' not in drone_data:
                # 默认白色
                color = (1.0, 1.0, 1.0)
            else:
                color = drone_data['color']
            
            # 转换为0-255整数
            channel_data = {
                "no": i,
                "c1": min(255, max(0, int(color[0] * 255))),
                "c2": min(255, max(0, int(color[1] * 255))),
                "c3": min(255, max(0, int(color[2] * 255)))
            }
            channel_frame["channels"].append(channel_data)
        
        if not channel_frame["channels"]:
            return None
            
        return channel_frame
    
    def get_drones_data(self, context, jsdm_tool):
        """获取无人机数据"""
        if jsdm_tool.export_mode == 'VERTICES':
            return self.get_drones_from_vertices(context, jsdm_tool)
        else:
            return self.get_drones_from_objects(context, jsdm_tool)
    
    def get_drones_from_objects(self, context, jsdm_tool=None):
        """从对象获取无人机数据"""
        drones = []
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if not hasattr(obj, 'location'):
                    continue
                    
                location = obj.matrix_world.translation.copy()
                color = self.get_drone_color(obj)
                
                drones.append({
                    'location': location,
                    'color': color,
                    'object': obj
                })
        return drones
    
    def get_drones_from_vertices(self, context, jsdm_tool):
        """从顶点获取无人机数据"""
        drones = []
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                mesh = obj.data
                matrix = obj.matrix_world.copy()
                
                # 获取物体的颜色
                obj_color = self.get_drone_color(obj)
                
                for i, vert in enumerate(mesh.vertices):
                    global_pos = matrix @ vert.co.copy()
                    
                    drones.append({
                        'location': global_pos,
                        'color': obj_color,  # 顶点模式使用物体颜色
                        'source_object': obj.name,
                        'vertex_index': i
                    })
        
        return drones
    
    def get_drone_color(self, obj):
        """获取无人机颜色"""
        default_color = (1.0, 1.0, 1.0, 1.0)
        
        if not obj:
            return default_color
        
        # 检查材质
        if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
            return default_color
        
        if not obj.data.materials:
            return default_color
        
        mat = obj.data.materials[0]
        if not mat:
            return default_color
        
        # 检查节点材质
        if not mat.use_nodes:
            if hasattr(mat, 'diffuse_color'):
                return mat.diffuse_color
            return default_color
        
        # 查找发射节点
        for node in mat.node_tree.nodes:
            if node.type == 'EMISSION':
                if 'Color' in node.inputs:
                    color = node.inputs['Color'].default_value
                    return (
                        max(0.0, min(1.0, color[0])),
                        max(0.0, min(1.0, color[1])),
                        max(0.0, min(1.0, color[2])),
                        1.0
                    )
        
        # 查找BSDF节点
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                if 'Base Color' in node.inputs:
                    color = node.inputs['Base Color'].default_value
                    return (
                        max(0.0, min(1.0, color[0])),
                        max(0.0, min(1.0, color[1])),
                        max(0.0, min(1.0, color[2])),
                        1.0
                    )
        
        return default_color
    
    def build_json_structure(self, drones_data, jsdm_tool, is_animation=False, frame_count=1, point_frames=None, channel_frames=None):
        """构建JSDM JSON数据结构 - 完全按照您提供的文件格式"""
        plane_count = len(drones_data)
        compatibility_mode = jsdm_tool.export_compatibility_mode
        
        # 构建metadata
        metadata = {
            "exported_from": "Blender",
            "blender_version": bpy.app.version_string,
            "compatibility_mode": compatibility_mode,
            "coordinate_system": "MAYA" if compatibility_mode == 'MAYA' else "BLENDER",
            "export_time": datetime.now().isoformat(),
            "export_mode": jsdm_tool.export_mode,
            "animation": is_animation,
            "export_colors": jsdm_tool.export_colors,
            "units": "meters",
            "scene_fps": jsdm_tool.scene_fps,
            "time_unit": "milliseconds",
            "version": "3.3.0",
            "note": f"导出兼容模式: {compatibility_mode}，时间单位: 毫秒"
        }
        
        # 构建JSON结构
        json_data = {
            "planeCount": plane_count,
            "name": self.filepath.replace('\\', '/'),
            "description": self.description or f"blender_export_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "frameCount": frame_count,
            "pointFrames": point_frames or [],
            "channelFrames": channel_frames or [],
            "droneTypes": [
                {
                    "no": i + 1,
                    "type": 21,
                    "cache": '["chuniaokj01"]'  # 与您提供的文件格式一致
                } for i in range(plane_count)
            ],
            "metadata": metadata
        }
        
        # 如果是静态导出，创建默认帧
        if not is_animation:
            point_frame = self.build_point_frame(drones_data, 0, jsdm_tool)
            json_data["pointFrames"].append(point_frame)
            
            if jsdm_tool.export_colors:
                channel_frame = self.build_channel_frame(drones_data, 0)
                if channel_frame:
                    json_data["channelFrames"].append(channel_frame)
        
        # 确保至少有一个pointFrame
        if not json_data["pointFrames"]:
            point_frame = self.build_point_frame(drones_data, 0, jsdm_tool)
            json_data["pointFrames"].append(point_frame)
        
        return json_data
    
    def invoke(self, context, event):
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if blend_filepath:
                base_name = os.path.splitext(blend_filepath)[0]
                self.filepath = base_name + ".jsdm"
            else:
                self.filepath = "drone_show.jsdm"
        
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        jsdm_tool.start_frame = scene.frame_start
        jsdm_tool.end_frame = scene.frame_end
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ==================== 其他操作符类 ====================

class JSDM_OT_show_export_settings(Operator):
    bl_idname = "jsdm.show_export_settings"
    bl_label = "显示/隐藏导出设置"
    bl_description = "显示或隐藏详细的导出设置选项"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        jsdm_tool.show_export_settings = not jsdm_tool.show_export_settings
        return {'FINISHED'}

class JSDM_OT_generate_mesh_lines(Operator):
    bl_idname = "jsdm.generate_mesh_lines"
    bl_label = "生成网格线"
    bl_description = "在选中的无人机之间生成网格线"
    
    def execute(self, context):
        drones = [obj for obj in context.selected_objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有选中无人机")
            return {'CANCELLED'}
        
        drones.sort(key=lambda x: x.name)
        
        collection_name = "Mesh_Lines"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)
        
        mesh = bpy.data.meshes.new("MeshLine")
        obj = bpy.data.objects.new("MeshLine", mesh)
        
        bm = bmesh.new()
        
        for drone in drones:
            bm.verts.new(drone.location)
        
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        
        for i in range(len(drones) - 1):
            if i < len(bm.verts) and (i + 1) < len(bm.verts):
                try:
                    bm.edges.new([bm.verts[i], bm.verts[i + 1]])
                except ValueError as e:
                    print(f"创建边时出错: {e}")
                    continue
        
        bm.to_mesh(mesh)
        bm.free()
        
        mat = bpy.data.materials.new(name="MeshLineMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (1.0, 0.5, 0.1, 1.0)
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        obj.data.materials.append(mat)
        
        collection.objects.link(obj)
        
        self.report({'INFO'}, f"已生成 {len(drones)} 架无人机的网格线")
        return {'FINISHED'}

class JSDM_OT_select_drones_by_order(Operator):
    bl_idname = "jsdm.select_drones_by_order"
    bl_label = "按编号选择"
    bl_description = "按无人机编号选择无人机"
    
    start_index: IntProperty(name="起始编号", default=1, min=1)
    end_index: IntProperty(name="结束编号", default=100, min=1)
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        
        selected_count = 0
        for obj in bpy.data.objects:
            if obj.name.startswith("drone_"):
                try:
                    drone_num = int(obj.name.split("_")[1])
                    if self.start_index <= drone_num <= self.end_index:
                        obj.select_set(True)
                        selected_count += 1
                except (IndexError, ValueError):
                    continue
        
        self.report({'INFO'}, f"已选择 {selected_count} 架无人机（编号 {self.start_index}-{self.end_index}）")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class JSDM_OT_clear_drones(Operator):
    bl_idname = "jsdm.clear_drones"
    bl_label = "清除无人机"
    bl_description = "清除所有无人机对象"
    
    def execute(self, context):
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        for drone in drones:
            bpy.data.objects.remove(drone, do_unlink=True)
        
        mats_to_remove = [mat for mat in bpy.data.materials if mat.name.startswith("drone_")]
        for mat in mats_to_remove:
            bpy.data.materials.remove(mat)
        
        self.report({'INFO'}, f"已清除 {len(drones)} 架无人机")
        return {'FINISHED'}

class JSDM_OT_clear_lines(Operator):
    bl_idname = "jsdm.clear_lines"
    bl_label = "清除网格线"
    bl_description = "清除所有生成的网格线"
    
    def execute(self, context):
        lines = [obj for obj in bpy.data.objects if "MeshLine" in obj.name]
        
        for line in lines:
            bpy.data.objects.remove(line, do_unlink=True)
        
        mats_to_remove = [mat for mat in bpy.data.materials if "MeshLine" in mat.name]
        for mat in mats_to_remove:
            bpy.data.materials.remove(mat)
        
        self.report({'INFO'}, f"已清除 {len(lines)} 条网格线")
        return {'FINISHED'}

class JSDM_OT_clear_all(Operator):
    bl_idname = "jsdm.clear_all"
    bl_label = "清除全部"
    bl_description = "清除所有无人机和网格线"
    
    def execute(self, context):
        bpy.ops.jsdm.clear_drones()
        bpy.ops.jsdm.clear_lines()
        
        if "Imported_Drones" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["Imported_Drones"])
        
        if "Mesh_Lines" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["Mesh_Lines"])
        
        self.report({'INFO'}, "已清除所有无人机和网格线")
        return {'FINISHED'}

class JSDM_OT_set_scene_fps(Operator):
    bl_idname = "jsdm.set_scene_fps"
    bl_label = "设置场景帧率"
    bl_description = "应用场景帧率设置"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        context.scene.render.fps = jsdm_tool.scene_fps
        context.scene.render.fps_base = 1.0
        self.report({'INFO'}, f"场景帧率已设置为: {jsdm_tool.scene_fps} fps")
        return {'FINISHED'}

class JSDM_OT_update_drone_size(Operator):
    bl_idname = "jsdm.update_drone_size"
    bl_label = "更新无人机尺寸"
    bl_description = "更新所有无人机的尺寸"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有找到无人机")
            return {'CANCELLED'}
        
        base_radius = 0.5
        scale_factor = jsdm_tool.drone_size / base_radius
            
        for drone in drones:
            drone.scale = (scale_factor, scale_factor, scale_factor)
            drone.keyframe_insert(data_path="scale", frame=context.scene.frame_current)
        
        self.report({'INFO'}, f"已更新 {len(drones)} 架无人机的尺寸")
        return {'FINISHED'}

class JSDM_OT_update_emission_strength(Operator):
    bl_idname = "jsdm.update_emission_strength"
    bl_label = "更新自发光强度"
    bl_description = "更新所有无人机的自发光强度"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        
        drone_materials = [mat for mat in bpy.data.materials if mat.name.startswith("drone_")]
        
        if not drone_materials:
            self.report({'WARNING'}, "没有找到无人机材质")
            return {'CANCELLED'}
        
        for mat in drone_materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'EMISSION':
                        node.inputs['Strength'].default_value = jsdm_tool.emission_strength
                        node.inputs['Strength'].keyframe_insert(data_path="default_value", frame=context.scene.frame_current)
        
        self.report({'INFO'}, f"已更新 {len(drone_materials)} 个材质的自发光强度")
        return {'FINISHED'}

class JSDM_OT_update_subdivision(Operator):
    bl_idname = "jsdm.update_subdivision"
    bl_label = "更新细分等级"
    bl_description = "更新所有无人机的细分等级"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有找到无人机")
            return {'CANCELLED'}
        
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=jsdm_tool.subdivision_level,
            radius=0.5,
            location=(0, 0, 0)
        )
        temp_drone = context.active_object
        new_base_mesh = temp_drone.data
        new_base_mesh.name = f"drone_base_mesh_subdiv_{jsdm_tool.subdivision_level}"
        
        bpy.data.objects.remove(temp_drone, do_unlink=True)
        
        for drone in drones:
            location = drone.location.copy()
            scale = drone.scale.copy()
            
            new_mesh = new_base_mesh.copy()
            old_mesh = drone.data
            drone.data = new_mesh
            
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)
            
            drone.location = location
            drone.scale = scale
        
        self.report({'INFO'}, f"已更新 {len(drones)} 架无人机的细分等级")
        return {'FINISHED'}

class JSDM_OT_create_drones_from_vertices(Operator):
    bl_idname = "jsdm.create_drones_from_vertices"
    bl_label = "从顶点创建无人机"
    bl_description = "从选中网格的顶点位置创建无人机"
    
    def execute(self, context):
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "请先选择一个或多个网格对象")
            return {'CANCELLED'}
        
        collection_name = "Vertex_Drones"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            scene.collection.children.link(collection)
        
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=jsdm_tool.subdivision_level,
            radius=0.5,
            location=(0, 0, 0)
        )
        temp_drone = context.active_object
        base_mesh = temp_drone.data
        base_mesh.name = f"drone_base_mesh_subdiv_{jsdm_tool.subdivision_level}"
        bpy.data.objects.remove(temp_drone, do_unlink=True)
        
        drone_count = 0
        for obj in selected_objects:
            mesh = obj.data
            matrix = obj.matrix_world.copy()
            
            for i, vert in enumerate(mesh.vertices):
                global_pos = matrix @ vert.co.copy()
                
                drone_name = f"drone_{drone_count + 1:06d}"
                drone = bpy.data.objects.new(drone_name, base_mesh.copy())
                
                drone.location = global_pos
                drone.display_type = 'SOLID'
                
                base_radius = 0.5
                scale_factor = jsdm_tool.drone_size / base_radius
                    
                drone.scale = (scale_factor, scale_factor, scale_factor)
                
                mat = bpy.data.materials.new(name=f"drone_{drone_count + 1:06d}_material")
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                nodes.clear()
                
                emission = nodes.new(type='ShaderNodeEmission')
                emission.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
                emission.inputs['Strength'].default_value = jsdm_tool.emission_strength
                
                output = nodes.new(type='ShaderNodeOutputMaterial')
                mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
                
                if len(drone.data.materials) == 0:
                    drone.data.materials.append(mat)
                else:
                    drone.data.materials[0] = mat
                
                collection.objects.link(drone)
                drone_count += 1
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        
        self.report({'INFO'}, f"已从顶点创建 {drone_count} 架无人机")
        return {'FINISHED'}

class JSDM_OT_zero_location(Operator):
    bl_idname = "jsdm.zero_location"
    bl_label = "位置归零"
    bl_description = "将选中物体的位置归零"
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "请先选择要归零位置的物体")
            return {'CANCELLED'}
        
        transformed_count = 0
        
        for obj in selected_objects:
            obj.location = (0.0, 0.0, 0.0)
            transformed_count += 1
        
        self.report({'INFO'}, f"已归零 {transformed_count} 个物体的位置")
        return {'FINISHED'}

class JSDM_OT_zero_rotation(Operator):
    bl_idname = "jsdm.zero_rotation"
    bl_label = "旋转归零"
    bl_description = "将选中物体的旋转归零"
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "请先选择要归零旋转的物体")
            return {'CANCELLED'}
        
        transformed_count = 0
        
        for obj in selected_objects:
            obj.rotation_euler = (0.0, 0.0, 0.0)
            obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
            transformed_count += 1
        
        self.report({'INFO'}, f"已归零 {transformed_count} 个物体的旋转")
        return {'FINISHED'}

class JSDM_OT_zero_scale(Operator):
    bl_idname = "jsdm.zero_scale"
    bl_label = "缩放归一"
    bl_description = "将选中物体的缩放归一"
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "请先选择要归一缩放的物体")
            return {'CANCELLED'}
        
        transformed_count = 0
        
        for obj in selected_objects:
            obj.scale = (1.0, 1.0, 1.0)
            transformed_count += 1
        
        self.report({'INFO'}, f"已归一 {transformed_count} 个物体的缩放")
        return {'FINISHED'}

# ==================== 面板类定义 ====================

class VIEW3D_PT_jsdm_tools(Panel):
    bl_label = "JSDM 工具"
    bl_idname = "VIEW3D_PT_jsdm_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "JSDM"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        # 导入/导出按钮
        row = layout.row()
        row.operator("import_scene.jsdm", text="导入JSDM", icon='IMPORT')
        row.operator("export_scene.jsdm", text="导出JSDM", icon='EXPORT')
        
        # 兼容模式设置
        box = layout.box()
        box.label(text="兼容模式:", icon='MODIFIER')
        
        row = box.row()
        row.label(text="导入:")
        row.prop(jsdm_tool, "import_compatibility_mode", text="")
        
        row = box.row()
        row.label(text="导出:")
        row.prop(jsdm_tool, "export_compatibility_mode", text="")
        
        # 基本设置
        box = layout.box()
        box.label(text="基本设置:", icon='SETTINGS')
        
        row = box.row()
        row.prop(jsdm_tool, "drone_size")
        row.operator("jsdm.update_drone_size", text="更新", icon='FILE_REFRESH')
        
        row = box.row()
        row.prop(jsdm_tool, "emission_strength")
        row.operator("jsdm.update_emission_strength", text="更新", icon='FILE_REFRESH')
        
        row = box.row()
        row.prop(jsdm_tool, "subdivision_level")
        row.operator("jsdm.update_subdivision", text="更新", icon='FILE_REFRESH')
        
        # 导入设置
        box = layout.box()
        box.label(text="导入设置:", icon='IMPORT')
        box.prop(jsdm_tool, "import_animation")
        box.prop(jsdm_tool, "import_colors")
        
        # 导出设置
        box = layout.box()
        box.label(text="导出设置:", icon='EXPORT')
        box.prop(jsdm_tool, "export_mode")
        
        # 显示/隐藏导出设置按钮
        row = box.row()
        row.operator("jsdm.show_export_settings", text="详细设置", icon='TRIA_DOWN' if jsdm_tool.show_export_settings else 'TRIA_RIGHT')
        
        # 导出设置详细选项
        if jsdm_tool.show_export_settings:
            box.prop(jsdm_tool, "export_animation")
            if jsdm_tool.export_animation:
                anim_box = box.box()
                anim_box.label(text="动画设置:", icon='ANIM')
                anim_box.prop(jsdm_tool, "start_frame")
                anim_box.prop(jsdm_tool, "end_frame")
                anim_box.prop(jsdm_tool, "frame_step")
            box.prop(jsdm_tool, "export_colors")
        
        # 场景设置
        box = layout.box()
        box.label(text="场景设置:", icon='SCENE_DATA')
        box.prop(jsdm_tool, "scene_fps")
        box.operator("jsdm.set_scene_fps", text="应用帧率设置")
        
        # 工具按钮
        box = layout.box()
        box.label(text="工具:", icon='TOOL_SETTINGS')
        
        row = box.row()
        row.operator("jsdm.generate_mesh_lines", text="生成网格线")
        row.operator("jsdm.select_drones_by_order", text="按编号选择")
        
        row = box.row()
        row.operator("jsdm.zero_location", text="位置归零")
        row.operator("jsdm.zero_rotation", text="旋转归零")
        
        row = box.row()
        row.operator("jsdm.zero_scale", text="缩放归一")
        row.operator("jsdm.create_drones_from_vertices", text="从顶点创建")
        
        # 性能设置
        box = layout.box()
        box.label(text="性能设置:", icon='PREFERENCES')
        box.prop(jsdm_tool, "batch_size")
        box.prop(jsdm_tool, "show_progress")
        
        # 清除工具
        box = layout.box()
        box.label(text="清除工具:", icon='TRASH')
        row = box.row()
        row.operator("jsdm.clear_drones", text="清除无人机")
        row.operator("jsdm.clear_lines", text="清除网格线")
        box.operator("jsdm.clear_all", text="清除全部")

# ==================== 注册和注销 ====================

classes = (
    JSDMExportProperties,
    IMPORT_OT_jsdm,
    EXPORT_OT_jsdm,
    JSDM_OT_show_export_settings,
    JSDM_OT_generate_mesh_lines,
    JSDM_OT_select_drones_by_order,
    JSDM_OT_clear_drones,
    JSDM_OT_clear_lines,
    JSDM_OT_clear_all,
    JSDM_OT_set_scene_fps,
    JSDM_OT_update_drone_size,
    JSDM_OT_update_emission_strength,
    JSDM_OT_update_subdivision,
    JSDM_OT_create_drones_from_vertices,
    JSDM_OT_zero_location,
    JSDM_OT_zero_rotation,
    JSDM_OT_zero_scale,
    VIEW3D_PT_jsdm_tools,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)
    
    bpy.types.Scene.jsdm_tool = bpy.props.PointerProperty(type=JSDMExportProperties)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    
    del bpy.types.Scene.jsdm_tool

if __name__ == "__main__":
    register()