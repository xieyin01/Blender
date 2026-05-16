bl_info = {
    "name": "无人机表演数据交换 (JSDM)",
    "author": "Your Name", 
    "version": (3, 1, 0),  # 更新到3.1.0版本
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
        encodings_to_try = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                
                if content.startswith('\ufeff'):
                    content = content[1:]
                
                data = json.loads(content)
                print(f"成功使用编码: {encoding}")
                return data
            except:
                continue
        
        # 最终尝试
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                # 清理非ASCII字符
                clean_content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
                data = json.loads(clean_content)
                print("使用清理后的数据成功")
                return data
        except Exception as e:
            raise Exception(f"无法读取文件: {e}")

class JSDM_Progress:
    def __init__(self, context, total_steps, message):
        self.context = context
        self.total_steps = total_steps
        self.current_step = 0
        self.message = message
        self.start_time = time.time()
        
        # 初始化进度条
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
        
        # 更新进度条
        if hasattr(self.context, 'window_manager'):
            wm = self.context.window_manager
            wm.progress_update(progress * 100)
        
        print(f"{self.message}: {int(progress*100)}% {step_message} {time_str}")
        return True
    
    def finish(self):
        """完成进度条"""
        if hasattr(self.context, 'window_manager'):
            wm = self.context.window_manager
            wm.progress_end()

class CoordinateSystemDetector:
    """修复：正确的坐标系检测和转换类，确保Blender和Maya兼容"""
    
    @staticmethod
    def detect_coordinate_system(data):
        """从数据中检测坐标系"""
        metadata = data.get('metadata', {})
        
        # 优先从元数据读取
        if 'coordinate_system' in metadata:
            system = metadata['coordinate_system'].upper()
            if system in ['BLENDER', 'MAYA']:
                return system
        
        # 通过数据分析检测
        point_frames = data.get('pointFrames', [])
        if point_frames:
            first_frame = point_frames[0]
            points = first_frame.get('points', [])
            if points:
                # 检查典型的Maya坐标特征（Y-up）
                for point in points[:10]:  # 检查前10个点
                    y = point.get('y', 0)
                    z = point.get('z', 0)
                    # 如果大部分点的Y值较大，可能是Maya坐标系
                    if abs(y) > abs(z) * 2:
                        return 'MAYA'
        
        return 'BLENDER'  # 默认Blender
    
    @staticmethod
    def convert_coordinates(location, source_system, target_system):
        """修复：正确的坐标系转换，确保双向兼容"""
        if source_system == target_system:
            return (location[0], location[1], location[2])
        
        x, y, z = location
        
        # Blender (Z-up) 到 Maya (Y-up) 的转换
        if source_system == 'BLENDER' and target_system == 'MAYA':
            # Blender: X-right, Y-forward, Z-up
            # Maya: X-right, Y-up, Z-forward (但Z方向相反)
            return (x, z, -y)
        
        # Maya (Y-up) 到 Blender (Z-up) 的转换  
        elif source_system == 'MAYA' and target_system == 'BLENDER':
            # Maya: X-right, Y-up, Z-forward (但Z方向相反)
            # Blender: X-right, Y-forward, Z-up
            return (x, -z, y)
        
        # 未知转换，保持原样
        return (x, y, z)
    
    @staticmethod
    def get_software_info():
        """获取软件信息用于元数据"""
        return {
            "blender_version": bpy.app.version_string,
            "software": "Blender",
            "coordinate_system": "BLENDER"
        }

class TimeUnitDetector:
    """检测时间单位并转换为帧号"""
    
    @staticmethod
    def detect_time_unit(point_frames):
        """检测时间单位（秒或毫秒）"""
        # 检查所有时间值
        all_times = []
        
        for frame in point_frames:
            if 'time' in frame:
                all_times.append(frame['time'])
        
        if not all_times:
            return 'seconds'  # 默认秒
        
        # 如果最大时间值大于100，可能是毫秒
        max_time = max(all_times)
        if max_time > 100:
            print(f"检测到最大时间值 {max_time}，使用毫秒单位")
            return 'milliseconds'
        else:
            print(f"检测到最大时间值 {max_time}，使用秒单位")
            return 'seconds'
    
    @staticmethod
    def time_to_frame(time_value, time_unit, fps=10):
        """将时间值转换为帧号"""
        if time_unit == 'milliseconds':
            # 毫秒转秒，然后乘以帧率
            seconds = time_value / 1000.0
            return int(seconds * fps) + 1  # 帧号从1开始
        else:
            # 秒直接乘以帧率
            return int(time_value * fps) + 1  # 帧号从1开始

# ==================== 属性类定义 ====================

class JSDMExportProperties(PropertyGroup):
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
    
    export_mode: EnumProperty(
        name="导出模式",
        description="选择导出数据源",
        items=[
            ('OBJECTS', "选中物体", "将选中的网格物体作为无人机"),
            ('VERTICES', "网格顶点", "将选中物体的顶点作为无人机位置"),
        ],
        default='OBJECTS'
    )
    
    import_animation: BoolProperty(
        name="导入动画",
        description="导入序列帧动画数据",
        default=True
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
    
    # 场景帧率设置
    scene_fps: IntProperty(
        name="场景帧率",
        description="设置场景帧率（帧/秒）- 影响动画速度",
        default=10,
        min=1,
        max=120
    )
    
    # 细分等级设置 - 替换性能模式
    subdivision_level: IntProperty(
        name="细分等级",
        description="无人机球体的细分等级（1=低质量，3=高质量）",
        default=2,
        min=1,
        max=4
    )
    
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
    
    line_thickness: FloatProperty(
        name="线条粗细",
        description="生成网格线的粗细",
        default=0.05,
        min=0.01,
        max=1.0
    )
    
    # 控制导出设置面板的显示
    show_export_settings: BoolProperty(
        name="显示导出设置",
        description="显示详细的导出设置选项",
        default=False  # 默认隐藏
    )

# ==================== 兼容性验证器 ====================

class CompatibilityValidator:
    """验证和确保Blender-Maya兼容性"""
    
    @staticmethod
    def validate_export_data(drones_data, jsdm_tool):
        """验证导出数据的兼容性"""
        issues = []
        warnings = []
        
        # 检查无人机数量
        if len(drones_data) == 0:
            issues.append("没有找到无人机数据")
        
        # 检查坐标范围（避免极端值）
        for i, drone in enumerate(drones_data[:100]):  # 只检查前100个
            if 'location' not in drone:
                issues.append(f"无人机 {i} 缺少位置数据")
                continue
                
            location = drone['location']
            for axis, value in enumerate(location):
                if abs(value) > 1000:  # 超过1000米可能有问题
                    warnings.append(f"无人机 {i} 的坐标值较大: {value}")
        
        return issues, warnings
    
    @staticmethod
    def apply_compatibility_fixes(data):
        """应用兼容性修复"""
        fixed_data = data.copy()
        
        # 默认开启Maya优化
        if 'metadata' not in fixed_data:
            fixed_data['metadata'] = {}
        fixed_data['metadata']['optimized_for_maya'] = True
        fixed_data['metadata']['maya_up_axis'] = 'Y'
        
        return fixed_data

# ==================== 高性能导入器 ====================

class HighPerformanceImporter:
    def __init__(self, context, jsdm_tool):
        self.context = context
        self.jsdm_tool = jsdm_tool
        self.base_meshes = {}  # 缓存不同细分等级的网格
        
    def create_base_mesh(self, subdivision_level=2):
        """创建基础无人机网格 - 根据细分等级"""
        if subdivision_level in self.base_meshes and self.base_meshes[subdivision_level].name in bpy.data.meshes:
            return self.base_meshes[subdivision_level]
        
        # 创建球体，使用指定的细分等级
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=subdivision_level,
            radius=0.5,
            location=(0, 0, 0)
        )
        drone_obj = self.context.active_object
        base_mesh = drone_obj.data
        base_mesh.name = f"drone_base_mesh_subdiv_{subdivision_level}"
        
        # 从场景中移除临时物体但保留网格
        bpy.data.objects.remove(drone_obj, do_unlink=True)
        
        # 缓存网格
        self.base_meshes[subdivision_level] = base_mesh
        
        return base_mesh
    
    def import_drones_batch(self, data, collection, coordinate_system):
        """批量导入无人机 - 支持序列帧动画"""
        start_time = time.time()
        
        # 获取数据
        point_frames = data.get("pointFrames", [])
        
        if not point_frames:
            return []
        
        # 检查是否有动画数据
        has_animation = len(point_frames) > 1 and self.jsdm_tool.import_animation
        
        if has_animation:
            print(f"检测到动画数据: {len(point_frames)} 位置帧")
            return self.import_animation_data(data, collection, coordinate_system)
        else:
            # 使用第一帧数据
            points = point_frames[0].get("points", [])
            
            if not points:
                return []
            
            return self.import_static_data(points, collection, coordinate_system)
    
    def import_static_data(self, points, collection, coordinate_system):
        """导入静态数据（单帧）"""
        start_time = time.time()
        
        total_drones = len(points)
        batch_size = self.jsdm_tool.batch_size
        
        print(f"开始导入 {total_drones} 架无人机（静态）")
        
        # 创建基础网格 - 根据细分等级
        base_mesh = self.create_base_mesh(self.jsdm_tool.subdivision_level)
        
        # 批量创建无人机
        drones = []
        
        # 设置进度条
        progress = None
        if self.jsdm_tool.show_progress:
            progress = JSDM_Progress(self.context, (total_drones + batch_size - 1) // batch_size, "导入无人机")
        
        # 分批处理
        for batch_start in range(0, total_drones, batch_size):
            batch_end = min(batch_start + batch_size, total_drones)
            batch_drones = self.create_drones_batch(
                points[batch_start:batch_end], 
                batch_start, 
                base_mesh, 
                coordinate_system
            )
            
            # 批量链接到集合
            for drone in batch_drones:
                collection.objects.link(drone)
            
            drones.extend(batch_drones)
            
            # 更新进度
            if progress:
                progress.update(f"已导入 {len(drones)}/{total_drones}")
        
        # 完成进度条
        if progress:
            progress.finish()
        
        end_time = time.time()
        print(f"✅ 静态导入完成: {len(drones)} 架无人机，耗时: {end_time - start_time:.2f}秒")
        
        return drones
    
    def import_animation_data(self, data, collection, coordinate_system):
        """修复：完整导入动画数据（多帧）- 只处理位置动画"""
        start_time = time.time()
        
        point_frames = data.get("pointFrames", [])
        
        # 检测时间单位
        time_unit = TimeUnitDetector.detect_time_unit(point_frames)
        fps = self.jsdm_tool.scene_fps
        
        print(f"时间单位: {time_unit}, 帧率: {fps} fps")
        
        # 计算总帧数
        total_position_frames = len(point_frames)
        
        # 计算实际时间轴帧数
        all_times = []
        for frame in point_frames:
            if 'time' in frame:
                all_times.append(TimeUnitDetector.time_to_frame(frame['time'], time_unit, fps))
        
        total_timeline_frames = max(all_times) if all_times else total_position_frames
        
        total_drones = len(point_frames[0].get("points", [])) if point_frames else 0
        
        print(f"开始导入动画数据: {total_drones} 架无人机")
        print(f"位置帧: {total_position_frames}, 时间轴帧: {total_timeline_frames}")
        
        # 创建基础网格 - 根据细分等级
        base_mesh = self.create_base_mesh(self.jsdm_tool.subdivision_level)
        
        # 创建无人机对象（使用第一帧位置）
        first_points = point_frames[0].get("points", [])
        
        drones = self.create_drones_batch(first_points, 0, base_mesh, coordinate_system)
        
        # 链接到集合
        for drone in drones:
            collection.objects.link(drone)
        
        # 设置进度条
        progress = None
        if self.jsdm_tool.show_progress:
            progress = JSDM_Progress(self.context, total_position_frames, "创建动画关键帧")
        
        # 修复：处理位置动画数据 - 使用实际时间值
        for point_frame in point_frames:
            time_value = point_frame.get("time", 0)
            timeline_frame = TimeUnitDetector.time_to_frame(time_value, time_unit, fps)
            
            # 设置当前帧
            self.context.scene.frame_set(timeline_frame)
            
            points = point_frame.get("points", [])
            
            # 更新每个无人机的位置
            for i in range(len(drones)):
                if i < len(points):
                    point_data = points[i]
                    x, y, z = point_data.get("x", 0), point_data.get("y", 0), point_data.get("z", 0)
                    location = self.convert_coordinates_back((x, y, z), coordinate_system)
                    
                    drone = drones[i]
                    drone.location = location
                    
                    # 插入位置关键帧
                    drone.keyframe_insert(data_path="location", frame=timeline_frame)
            
            # 更新进度
            if progress:
                progress.update(f"位置帧 {time_value}")
        
        # 完成进度条
        if progress:
            progress.finish()
        
        # 自动设置时间轴范围
        self.context.scene.frame_start = 1
        self.context.scene.frame_end = total_timeline_frames
        
        end_time = time.time()
        print(f"✅ 动画导入完成: {len(drones)} 架无人机, {total_timeline_frames} 时间轴帧, 耗时: {end_time - start_time:.2f}秒")
        print(f"📊 时间轴设置为: 第 1 帧 到 第 {total_timeline_frames} 帧")
        print(f"🎯 关键帧统计: 位置 {total_position_frames} 帧")
        
        return drones
    
    def create_drones_batch(self, points, start_index, base_mesh, coordinate_system):
        """创建单个批次的无人机 - 编号从1开始"""
        drones = []
        
        for i, point_data in enumerate(points):
            # 获取位置
            x, y, z = point_data.get("x", 0), point_data.get("y", 0), point_data.get("z", 0)
            location = self.convert_coordinates_back((x, y, z), coordinate_system)
            
            # 创建无人机对象 - 编号从1开始
            drone_name = f"drone_{start_index + i + 1:06d}"
            
            # 每个无人机都有独立的网格副本
            drone = bpy.data.objects.new(drone_name, base_mesh.copy())
                
            drone.location = location
            drone.display_type = 'SOLID'
            
            # 应用无人机尺寸缩放
            base_radius = 0.5  # 球体基础半径为0.5
            scale_factor = self.jsdm_tool.drone_size / base_radius
                
            drone.scale = (scale_factor, scale_factor, scale_factor)
            
            # 设置默认白色材质
            self.set_drone_material(drone, start_index + i + 1)
            
            drones.append(drone)
        
        return drones
    
    def set_drone_material(self, drone, index):
        """为每个无人机创建材质"""
        # 每个无人机都有独立的材质
        mat_name = f"drone_{index:06d}_material"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # 创建自发光材质 - 只使用自发光节点
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # 白色
        emission.inputs['Strength'].default_value = self.jsdm_tool.emission_strength
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        
        # 直接连接到输出节点，只使用自发光
        mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
        # 应用到无人机
        if len(drone.data.materials) == 0:
            drone.data.materials.append(mat)
        else:
            drone.data.materials[0] = mat
    
    def convert_coordinates_back(self, location, coordinate_system):
        """修复：正确的坐标系转换回Blender"""
        x, y, z = location
        
        # 使用修复的坐标系转换
        if coordinate_system == 'MAYA':
            return CoordinateSystemDetector.convert_coordinates((x, y, z), 'MAYA', 'BLENDER')
        else:
            return (x, y, z)

# ==================== 操作符类定义 ====================

class IMPORT_OT_jsdm(Operator):
    bl_idname = "import_scene.jsdm"
    bl_label = "导入JSDM"
    bl_description = "导入无人机表演数据，支持序列帧动画"
    
    filename_ext = ".jsdm"
    filter_glob: StringProperty(default="*.jsdm", options={'HIDDEN'})
    filepath: StringProperty(name="文件路径", maxlen=1024, default="")

    def execute(self, context):
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        try:
            data = FileEncodingDetector.read_json_file(self.filepath)
            
            if not self.validate_jsdm_data(data):
                self.report({'ERROR'}, "无效的JSDM文件格式")
                return {'CANCELLED'}
            
            # 检查动画数据
            point_frames = data.get("pointFrames", [])
            has_animation = len(point_frames) > 1
            
            if has_animation and not jsdm_tool.import_animation:
                self.report({'INFO'}, f"检测到 {len(point_frames)} 帧动画数据，但未启用动画导入")
            
            # 创建无人机集合 - 默认始终创建
            collection_name = "Imported_Drones"
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
            else:
                collection = bpy.data.collections.new(collection_name)
                scene.collection.children.link(collection)
            
            # 获取坐标系信息 - 使用增强的检测
            coordinate_system = CoordinateSystemDetector.detect_coordinate_system(data)
            
            print(f"检测到坐标系: {coordinate_system}")
            
            # 使用高性能导入
            importer = HighPerformanceImporter(context, jsdm_tool)
            created_drones = importer.import_drones_batch(data, collection, coordinate_system)
            
            # 选择所有创建的无人机
            bpy.ops.object.select_all(action='DESELECT')
            for drone in created_drones:
                drone.select_set(True)
            
            drone_count = len(created_drones)
            
            # 显示状态信息
            if has_animation and jsdm_tool.import_animation:
                position_frames = len(point_frames)
                
                animation_info = f"，位置{position_frames}帧"
                
                # 自动设置时间轴范围
                scene.frame_start = 1
                scene.frame_end = position_frames
                
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
        required_fields = ['planeCount', 'pointFrames']
        for field in required_fields:
            if field not in data:
                print(f"缺少必要字段: {field}")
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

class EXPORT_OT_jsdm(Operator):
    bl_idname = "export_scene.jsdm"
    bl_label = "导出JSDM"
    bl_description = "导出无人机表演数据为JSDM格式"
    
    filename_ext = ".jsdm"
    filter_glob: StringProperty(default="*.jsdm", options={'HIDDEN'})
    filepath: StringProperty(name="文件路径", maxlen=1024, default="")
    description: StringProperty(name="描述", default="")
    
    def execute(self, context):
        scene = context.scene
        jsdm_tool = scene.jsdm_tool
        
        # 验证帧范围
        if jsdm_tool.export_animation:
            if jsdm_tool.start_frame > jsdm_tool.end_frame:
                self.report({'ERROR'}, "开始帧不能大于结束帧")
                return {'CANCELLED'}
        
        start_time = time.time()
        
        # 使用智能兼容模式
        final_system = 'BLENDER'
        file_compatibility = 'UNIVERSAL'
        
        print(f"导出坐标系: {final_system}, 兼容性模式: {file_compatibility}")
        
        try:
            # 构建JSON数据
            if jsdm_tool.export_animation:
                json_data = self.build_jsdm_animation_data(context, jsdm_tool, final_system)
            else:
                json_data = self.build_jsdm_static_data(context, jsdm_tool, final_system)
            
            if not json_data:
                self.report({'ERROR'}, "没有找到有效的无人机数据")
                return {'CANCELLED'}
            
            # 应用兼容性修复
            json_data = CompatibilityValidator.apply_compatibility_fixes(json_data)
            
            # 写入文件
            file_path = self.filepath.replace('\\', '/')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            end_time = time.time()
            frame_count = json_data.get("frameCount", 1)
            drone_count = json_data.get("planeCount", 0)
            
            # 显示导出统计信息
            if jsdm_tool.export_animation:
                # 使用实际导出的帧数
                point_frames = json_data.get("pointFrames", [])
                
                position_frames = len(point_frames)
                
                frame_info = f"（实际导出: 位置{position_frames}帧）"
            else:
                frame_info = ""
            
            self.report({'INFO'}, f"成功导出 {drone_count} 架无人机 {frame_count} 帧数据{frame_info}，耗时 {end_time-start_time:.1f}秒")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def build_jsdm_static_data(self, context, jsdm_tool, coordinate_system):
        """构建静态JSDM数据（单帧）"""
        drones_data = self.get_drones_data_batch(context, jsdm_tool)
        if not drones_data:
            return None
        
        return self.build_json_structure(drones_data, jsdm_tool, coordinate_system, False)
    
    def build_jsdm_animation_data(self, context, jsdm_tool, coordinate_system):
        """修复：构建动画JSDM数据（多帧）- 只导出位置数据"""
        original_frame = context.scene.frame_current
        
        # 获取第一帧确定无人机数量
        context.scene.frame_set(jsdm_tool.start_frame)
        first_frame_data = self.get_drones_data_batch(context, jsdm_tool)
        
        if not first_frame_data:
            context.scene.frame_set(original_frame)
            return None
        
        plane_count = len(first_frame_data)
        point_frames = []
        
        total_frames = (jsdm_tool.end_frame - jsdm_tool.start_frame) // jsdm_tool.frame_step + 1
        
        print(f"导出设置: 完整导出每一帧")
        
        # 创建进度条
        progress = None
        if jsdm_tool.show_progress:
            progress = JSDM_Progress(context, total_frames, "导出动画帧")
        
        frame_index = 0
        for frame in range(jsdm_tool.start_frame, jsdm_tool.end_frame + 1, jsdm_tool.frame_step):
            context.scene.frame_set(frame)
            
            # 更新进度
            if progress and not progress.update(f"帧 {frame}"):
                context.scene.frame_set(original_frame)
                return None
            
            # 修复：强制更新依赖图以确保正确数据
            context.view_layer.update()
            
            drones_data = self.get_drones_data_batch(context, jsdm_tool)
            
            if len(drones_data) != plane_count:
                print(f"警告: 帧 {frame} 无人机数量不一致，跳过")
                continue
            
            time_val = (frame - jsdm_tool.start_frame) / context.scene.render.fps
            
            # 只导出位置数据
            point_frame = self.build_frame_data(
                drones_data, time_val, coordinate_system
            )
            
            point_frames.append(point_frame)
            
            frame_index += 1
        
        # 完成进度条
        if progress:
            progress.finish()
        
        context.scene.frame_set(original_frame)
        
        # 使用实际导出的帧数
        actual_frame_count = len(point_frames)
        
        if actual_frame_count == 0:
            return None
        
        return self.build_json_structure(first_frame_data, jsdm_tool, coordinate_system, True, actual_frame_count, point_frames)
    
    def build_frame_data(self, drones_data, time_val, coordinate_system):
        """构建单帧数据 - 只导出位置"""
        point_frame = {"time": round(time_val, 3), "points": []}
        
        for i, drone_data in enumerate(drones_data, 1):
            # 修复：检查数据完整性
            if 'location' not in drone_data:
                continue
                
            location = drone_data['location']
            
            # 位置数据
            converted_location = CoordinateSystemDetector.convert_coordinates(
                location, 'BLENDER', coordinate_system
            )
            point_data = {
                "x": round(converted_location[0], 3),
                "y": round(converted_location[1], 3),
                "z": round(converted_location[2], 3),
                "no": i
            }
            point_frame["points"].append(point_data)
        
        return point_frame
    
    def get_drones_data_batch(self, context, jsdm_tool):
        """批量获取无人机数据"""
        if jsdm_tool.export_mode == 'VERTICES':
            return self.get_drones_from_vertices_batch(context)
        else:
            return self.get_drones_from_objects_batch(context)
    
    def get_drones_from_objects_batch(self, context):
        """批量从物体获取无人机数据"""
        drones = []
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # 修复：确保有位置数据
                if not hasattr(obj, 'location'):
                    continue
                    
                location = obj.matrix_world.translation.copy()
                    
                drones.append({
                    'location': location
                })
        return drones
    
    def get_drones_from_vertices_batch(self, context):
        """批量从顶点获取无人机数据"""
        drones = []
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                mesh = obj.data
                matrix = obj.matrix_world.copy()
                
                # 批量处理所有顶点
                for i, vert in enumerate(mesh.vertices):
                    global_pos = matrix @ vert.co.copy()
                    
                    drones.append({
                        'location': global_pos,
                        'source_object': obj.name,
                        'vertex_index': i
                    })
        
        return drones
    
    def build_json_structure(self, drones_data, jsdm_tool, coordinate_system, is_animation=False, frame_count=1, point_frames=None):
        """构建JSON数据结构 - 修复：添加空的channelFrames以兼容Maya"""
        plane_count = len(drones_data)
        
        # 获取软件信息
        software_info = CoordinateSystemDetector.get_software_info()
        
        json_data = {
            "planeCount": plane_count,
            "name": self.filepath.replace('\\', '/'),
            "description": self.description or f"blender_export_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "frameCount": frame_count,
            "pointFrames": point_frames or [],
            # 修复：添加空的channelFrames以兼容Maya导入脚本
            "channelFrames": [],
            "droneTypes": [{"no": str(i+1), "type": 21} for i in range(plane_count)],
            "metadata": {
                "exported_from": "Blender",
                "blender_version": bpy.app.version_string,
                "coordinate_system": coordinate_system,
                "export_time": datetime.now().isoformat(),
                "export_mode": jsdm_tool.export_mode,
                "animation": is_animation,
                "units": "meters",
                "scene_fps": jsdm_tool.scene_fps,
                "file_compatibility": "UNIVERSAL",
                "optimize_for_maya": True,
                "maya_up_axis": 'Y',
                "time_units": "seconds",
                "version": "3.1.0",  # 更新版本信息
                "note": "颜色数据已移除，channelFrames为空数组"  # 添加说明
            }
        }
        
        # 如果是单帧，添加单帧数据
        if not is_animation:
            point_frame = self.build_frame_data(drones_data, 0, coordinate_system)
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
        
        # 设置默认帧范围
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
        # 查找所有无人机
        drones = [obj for obj in context.selected_objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有选中无人机")
            return {'CANCELLED'}
        
        # 按名称排序无人机
        drones.sort(key=lambda x: x.name)
        
        # 创建网格线集合
        collection_name = "Mesh_Lines"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)
        
        # 创建网格线
        mesh = bpy.data.meshes.new("MeshLine")
        obj = bpy.data.objects.new("MeshLine", mesh)
        
        # 创建几何数据
        bm = bmesh.new()
        
        # 添加顶点
        for drone in drones:
            bm.verts.new(drone.location)
        
        # 修复：确保查找表已更新
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        
        # 添加边（连接相邻无人机）
        for i in range(len(drones) - 1):
            if i < len(bm.verts) and (i + 1) < len(bm.verts):
                try:
                    bm.edges.new([bm.verts[i], bm.verts[i + 1]])
                except ValueError as e:
                    print(f"创建边时出错: {e}")
                    continue
        
        # 更新网格
        bm.to_mesh(mesh)
        bm.free()
        
        # 设置网格线材质
        mat = bpy.data.materials.new(name="MeshLineMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (1.0, 0.5, 0.1, 1.0)  # 橙色
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        obj.data.materials.append(mat)
        
        # 添加到集合
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
        # 取消选择所有对象
        bpy.ops.object.select_all(action='DESELECT')
        
        # 选择指定编号范围内的无人机
        selected_count = 0
        for obj in bpy.data.objects:
            if obj.name.startswith("drone_"):
                try:
                    # 从名称中提取编号
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
        # 查找所有无人机
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        # 删除无人机
        for drone in drones:
            bpy.data.objects.remove(drone, do_unlink=True)
        
        # 清理无人机的材质
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
        # 查找所有网格线
        lines = [obj for obj in bpy.data.objects if "MeshLine" in obj.name]
        
        # 删除网格线
        for line in lines:
            bpy.data.objects.remove(line, do_unlink=True)
        
        # 清理网格线材质
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
        # 清除无人机
        bpy.ops.jsdm.clear_drones()
        # 清除网格线
        bpy.ops.jsdm.clear_lines()
        
        # 删除无人机集合
        if "Imported_Drones" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["Imported_Drones"])
        
        # 删除网格线集合
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
        
        # 查找所有无人机对象
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有找到无人机")
            return {'CANCELLED'}
        
        # 更新所有无人机的尺寸
        base_radius = 0.5  # 球体基础半径为0.5
        scale_factor = jsdm_tool.drone_size / base_radius
            
        for drone in drones:
            drone.scale = (scale_factor, scale_factor, scale_factor)
            # 确保缩放被应用
            drone.keyframe_insert(data_path="scale", frame=context.scene.frame_current)
        
        self.report({'INFO'}, f"已更新 {len(drones)} 架无人机的尺寸")
        return {'FINISHED'}

class JSDM_OT_update_emission_strength(Operator):
    bl_idname = "jsdm.update_emission_strength"
    bl_label = "更新自发光强度"
    bl_description = "更新所有无人机的自发光强度"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        
        # 查找所有无人机材质
        drone_materials = [mat for mat in bpy.data.materials if mat.name.startswith("drone_")]
        
        if not drone_materials:
            self.report({'WARNING'}, "没有找到无人机材质")
            return {'CANCELLED'}
        
        # 更新所有无人机材质的自发光强度
        for mat in drone_materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'EMISSION':
                        node.inputs['Strength'].default_value = jsdm_tool.emission_strength
                        # 在当前帧插入关键帧
                        node.inputs['Strength'].keyframe_insert(data_path="default_value", frame=context.scene.frame_current)
        
        self.report({'INFO'}, f"已更新 {len(drone_materials)} 个材质的自发光强度")
        return {'FINISHED'}

class JSDM_OT_update_subdivision(Operator):
    bl_idname = "jsdm.update_subdivision"
    bl_label = "更新细分等级"
    bl_description = "更新所有无人机的细分等级"
    
    def execute(self, context):
        jsdm_tool = context.scene.jsdm_tool
        
        # 查找所有无人机对象
        drones = [obj for obj in bpy.data.objects if obj.name.startswith("drone_")]
        
        if not drones:
            self.report({'WARNING'}, "没有找到无人机")
            return {'CANCELLED'}
        
        # 创建新的基础网格
        importer = HighPerformanceImporter(context, jsdm_tool)
        new_base_mesh = importer.create_base_mesh(jsdm_tool.subdivision_level)
        
        # 更新所有无人机的网格
        for drone in drones:
            # 保存当前位置和缩放
            location = drone.location.copy()
            scale = drone.scale.copy()
            
            # 创建新的网格副本
            new_mesh = new_base_mesh.copy()
            
            # 替换无人机的网格
            old_mesh = drone.data
            drone.data = new_mesh
            
            # 清理旧网格
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)
            
            # 恢复位置和缩放
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
        
        # 检查是否有选中的网格对象
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "请先选择一个或多个网格对象")
            return {'CANCELLED'}
        
        # 创建无人机集合
        collection_name = "Vertex_Drones"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            scene.collection.children.link(collection)
        
        # 创建基础网格 - 根据细分等级
        importer = HighPerformanceImporter(context, jsdm_tool)
        base_mesh = importer.create_base_mesh(jsdm_tool.subdivision_level)
        
        # 创建无人机
        drone_count = 0
        for obj in selected_objects:
            mesh = obj.data
            matrix = obj.matrix_world.copy()
            
            # 处理所有顶点
            for i, vert in enumerate(mesh.vertices):
                global_pos = matrix @ vert.co.copy()
                
                # 创建无人机对象 - 编号从1开始
                drone_name = f"drone_{drone_count + 1:06d}"
                
                # 每个无人机都有独立的网格副本
                drone = bpy.data.objects.new(drone_name, base_mesh.copy())
                
                drone.location = global_pos
                drone.display_type = 'SOLID'
                
                # 应用无人机尺寸缩放
                base_radius = 0.5  # 球体基础半径为0.5
                scale_factor = jsdm_tool.drone_size / base_radius
                    
                drone.scale = (scale_factor, scale_factor, scale_factor)
                
                # 设置默认白色材质
                importer.set_drone_material(drone, drone_count + 1)
                
                # 添加到集合
                collection.objects.link(drone)
                drone_count += 1
        
        # 选择所有创建的无人机
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        
        self.report({'INFO'}, f"已从顶点创建 {drone_count} 架无人机")
        return {'FINISHED'}

# ==================== 三个独立的变换归零操作符 ====================

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
            # 位置归零
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
            # 旋转归零
            obj.rotation_euler = (0.0, 0.0, 0.0)
            obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)  # 四元数单位旋转
            obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)  # 轴角表示
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
            # 缩放归一
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
        
        # 基本设置
        box = layout.box()
        box.label(text="基本设置:", icon='SETTINGS')
        
        # 无人机尺寸设置
        row = box.row()
        row.prop(jsdm_tool, "drone_size")
        row.operator("jsdm.update_drone_size", text="更新", icon='FILE_REFRESH')
        
        # 自发光强度设置
        row = box.row()
        row.prop(jsdm_tool, "emission_strength")
        row.operator("jsdm.update_emission_strength", text="更新", icon='FILE_REFRESH')
        
        # 细分等级设置
        row = box.row()
        row.prop(jsdm_tool, "subdivision_level")
        row.operator("jsdm.update_subdivision", text="更新", icon='FILE_REFRESH')
        
        # 导入设置
        box = layout.box()
        box.label(text="导入设置:", icon='IMPORT')
        box.prop(jsdm_tool, "import_animation")
        
        # 导出设置
        box = layout.box()
        box.label(text="导出设置:", icon='EXPORT')
        box.prop(jsdm_tool, "export_mode")
        
        # 显示/隐藏导出设置按钮
        row = box.row()
        row.operator("jsdm.show_export_settings", text="详细设置", icon='TRIA_DOWN' if jsdm_tool.show_export_settings else 'TRIA_RIGHT')
        
        # 导出设置详细选项
        if jsdm_tool.show_export_settings:
            # 动画设置
            box.prop(jsdm_tool, "export_animation")
            if jsdm_tool.export_animation:
                anim_box = box.box()
                anim_box.label(text="动画设置:", icon='ANIM')
                anim_box.prop(jsdm_tool, "start_frame")
                anim_box.prop(jsdm_tool, "end_frame")
                anim_box.prop(jsdm_tool, "frame_step")
        
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
            # 如果类已经注册，先取消注册再重新注册
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