"""
导出操作符
处理JSDM格式的导出功能
"""

import bpy
import json
import os
import time
import base64
import math
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty

from ..config import __addon_name__, ERROR_MESSAGES
from ..util.geometry_nodes_reader import GeometryNodesReader, get_spreadsheet_summary


class PCJSDM_OT_Export(Operator, ExportHelper):
    """导出几何节点JSDM格式"""
    
    bl_idname = "pc_export_pointcloud.jsdm"
    bl_label = "导出JSDM"
    bl_description = "导出几何节点JSDM格式数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 文件选择器属性
    filename_ext = ".jsdm"
    filter_glob: StringProperty(
        default="*.jsdm",
        options={'HIDDEN'}
    )
    
    # 导出设置
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

    # 元数据设置
    project_name: StringProperty(
        name="项目名称",
        description="项目或文件名称",
        default=""
    )
    
    description: StringProperty(
        name="描述",
        description="项目描述",
        default=""
    )
    
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

    #用于跟踪进度的属性
    _progress_callback = None

    
    def execute(self, context):
        """执行导出操作"""
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, ERROR_MESSAGES['NO_OBJECT_SELECTED'])
            return {'CANCELLED'}
        
        # 检查几何节点
        reader = GeometryNodesReader(obj)
        if not reader.has_geometry_nodes():
            self.report({'ERROR'}, ERROR_MESSAGES['NO_GEOMETRY_NODES'])
            return {'CANCELLED'}
        
        try:
            start_time = time.time()

            #检查动画帧范围
            if self.export_animation and self.frame_end < self.frame_start:
                self.report({'ERROR'}, "动画帧范围无效")
                return {'CANCELLED'}
            
            # 获取几何节点数据
            if self.export_animation:
                jsdm_data = self._export_animation_data(context,obj,reader)

            else:
                jsdm_data = self._export_single_frame_data(obj, reader)

            if not jsdm_data:
                self.report({'ERROR'},"没有找到几何节点数据")
                return {'CANCELLED'}
            
            # 保存文件
            export_path = self.filepath
            if not export_path.endswith(self.filename_ext):
                export_path += self.filename_ext
            
            # 确保目录存在
            directory = os.path.dirname(os.path.abspath(export_path))
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # 使用更安全的 JSON 序列化
            try:
                with open(export_path, 'w', encoding='utf-8') as f:
                    # 使用自定义的序列化函数处理特殊类型
                    json.dump(jsdm_data, f, indent=2, ensure_ascii=False, default=self._json_default)
                
                # 验证文件是否成功保存
                if not os.path.exists(export_path):
                    raise Exception("文件保存失败")
                    
                file_size = os.path.getsize(export_path)
                if file_size == 0:
                    raise Exception("文件为空")
                
            except Exception as e:
                self.report({'ERROR'}, f"保存文件失败: {str(e)}")
                return {'CANCELLED'}
            
            # 报告结果
            elapsed_time = time.time() - start_time
            point_count = jsdm_data.get('planeCount', 0)
            frame_count = jsdm_data.get('frameCount', 1)
            
            message = f"成功导出 {point_count} 点到 {os.path.basename(export_path)} "
            if self.export_animation:
                message += f"({frame_count}帧, {elapsed_time:.2f}秒)"
            else:
                message += f"({elapsed_time:.2f}秒)"
            
            self.report({'INFO'}, message)
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, ERROR_MESSAGES['EXPORT_FAILED'].format(str(e)))
            import traceback
            print(f"详细错误信息:")
            traceback.print_exc()
            return {'CANCELLED'}
        
    def _json_default(self, obj):
        """JSON 序列化的默认处理器"""
        if isinstance(obj, (bpy.types.Object, bpy.types.Material, bpy.types.Image)):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, complex):
            return [obj.real, obj.imag]
        elif isinstance(obj, (float, np.floating)):
            # 处理 NaN 和 Inf
            if math.isnan(obj):
                return 0.0
            elif math.isinf(obj):
                return 1e10 if obj > 0 else -1e10
            return obj
        else:
            return str(obj)

    def _export_single_frame_data(self, obj, reader):
        """导出静态数据"""
        spreadsheet_data = reader.get_spreadsheet_data()

        if not spreadsheet_data or not spreadsheet_data.get('positions'):
            print(f"警告：未找到位置数据，数据键: {list(spreadsheet_data.keys())}")
            return None
        
        print(f"获取到 {len(spreadsheet_data.get('positions', []))} 个位置点")
        
        #构建JSDM数据
        jsdm_data = self._build_jsdm_data(spreadsheet_data, obj,is_animation=False)
        return jsdm_data
    
    def _export_animation_data(self, context, obj, reader):
        """导出动画数据"""
        original_frame = context.scene.frame_current
        original_frame_start = context.scene.frame_start
        original_frame_end = context.scene.frame_end

        try:
            channel_frames = []
            point_frames = []
            frame_rate = context.scene.render.fps / context.scene.render.fps_base

            #计算总帧数
            total_frames = (self.frame_end - self.frame_start + 1)//self.frame_step

            if total_frames <= 0 :
                total_frames = 1

            #减少进度报告的频率
            report_interval = max(1, total_frames // 10) #最多报告10次

            print(f"开始导出动画，共{total_frames}帧")

            #逐帧导出动画
            for frame_index,frame in enumerate(range(self.frame_start, self.frame_end + 1, self.frame_step)):

                #设置当前帧
                context.scene.frame_set(frame)

                depsgraph = bpy.context.evaluated_depsgraph_get()
                depsgraph.update()

                #更新进度显示,只在特定间隔报告进度，减少UI更新
                if frame_index % report_interval == 0: 
                    progress = (frame_index + 1)/total_frames * 100
                    print(f"导出进度: {progress:.1f}% ({frame_index + 1}/{total_frames} 帧)")

                #获取当前帧的数据
                spreadsheet_data = reader.get_spreadsheet_data()
                if not spreadsheet_data or not spreadsheet_data.get('positions'):
                    continue

                #计算时间
                time_ms = int((frame - self.frame_start) * (1000 / frame_rate))

                #构建当前帧的颜色和位置数据
                channel_frame,point_frame = self._build_point_frame(
                    spreadsheet_data, 
                    time_ms,
                    frame
                )
                if channel_frame: 
                    channel_frames.append(channel_frame)
                if point_frame:
                    point_frames.append(point_frame)
            
            if not channel_frames or not point_frames:
                return None
            #构建完整的JSDM数据结构
            plane_count = len(point_frames[0]['points']) if point_frames else 0

            metadata = self._build_metadata(
                object_name=obj.name,
                frame_rate = frame_rate,
                is_animation = True
            )

            jsdm_data = {
                "planeCount": plane_count,
                "name":self.project_name if self.project_name else os.path.basename(self.filepath),
                "description": "self.description",
                "frameCount": total_frames,
                "channelFrames": channel_frames,
                "pointFrames": point_frames,
                "droneTypes": self._build_drone_types(plane_count),
                "metadata": metadata,
            }

            return jsdm_data
        
        except Exception as e:
            raise Exception(f"导出动画数据时出错: {str(e)}")
        
        finally:
            #恢复原始帧设置
            context.scene.frame_set(original_frame)
            context.scene.frame_start = original_frame_start
            context.scene.frame_end = original_frame_end

    
    def _convert_coordinate_system(self, position, source_system='BLENDER', target_system='BLENDER', scale_factor=1.0):
        """转换坐标系"""
        x, y, z = position[0], position[1], position[2]
        
        if source_system == target_system:
            return [x * scale_factor, y * scale_factor, z * scale_factor]
        
        # 转换到中间坐标系 (Blender)
        if source_system == 'BLENDER':
            blender_coords = [x, y, z]
        elif source_system == 'MAYA':
            blender_coords = [x, z, -y]
        else:
            blender_coords = [x, y, z]
        
        # 从Blender转换到目标坐标系
        if target_system == 'BLENDER':
            result = blender_coords
        elif target_system == 'MAYA':
            result = [blender_coords[0], -blender_coords[2], blender_coords[1]]
        else:
            result = blender_coords
        
        return [
            result[0] * scale_factor,
            result[1] * scale_factor,
            result[2] * scale_factor
        ]
    
    def _build_point_frame(self, spreadsheet_data, time_ms, frame_number):   
        """构建单帧点数据""" 
        positions = spreadsheet_data.get('positions', [])
        colors = spreadsheet_data.get('colors', [])
        ids = spreadsheet_data.get('ids', [])

        if not positions:
            print(f"警告：没有位置数据，无法构建帧数据")
            return None, None
        
        # 添加数据验证 - 确保positions是列表且每个元素是长度为3的列表/元组
        if not isinstance(positions, (list, tuple)):
            print(f"警告：位置数据不是列表或元组，而是{type(positions)}")
            return None, None
        
        # 验证每个位置是否包含三个数值
        valid_positions = []
        for i, pos in enumerate(positions):
            try:
                # 确保每个位置有三个值
                if isinstance(pos, (list, tuple)) and len(pos) == 3:
                    valid_positions.append(pos)
                else:
                    print(f"警告：位置数据索引{i}格式错误，跳过该点: {pos}")
                    continue
            except Exception as e:
                print(f"警告：处理位置数据索引{i}时出错: {e}")
                continue
        
        if not valid_positions:
            print(f"警告：没有有效的位置数据")
            return None, None
    
        print(f"构建帧数据: {len(positions)} 个位置点")

        # 更新positions为有效数据
        positions = valid_positions

        #构建ChannelFrame数据(颜色和位置数据)
        channel_frame = {
            "time":float(time_ms),
            "channels": []
        }

        point_frame = {
            "time":float(time_ms),
            "points": []
        }


        #转换坐标系
        converted_positions = []
        for pos in positions:
            converted = self._convert_coordinate_system(
                pos,
                'BLENDER',
                self.coordinate_system,
                self.scale_factor
            )
            converted_positions.append(converted)
        
        #填充数据
        for i, pos in enumerate(converted_positions):
            point = {
                "x": float(pos[0]),
                "y": float(pos[1]),
                "z": float(pos[2])
            }
            
            # 添加ID
            if self.include_ids and i<len(ids):
                point["no"] = int(ids[i])
            elif self.include_ids:
                point["no"] = i + 1

            point_frame["points"].append(point)

            #添加颜色通道
            channel = {}
            
            #添加ID
            if self.include_ids and i <len(ids):
                channel["no"] = int(ids[i])
            elif self.include_ids:  # 添加默认ID
                channel["no"] = i + 1
            
            # 添加颜色
            if self.include_colors and  colors and i <len(colors):
                color = colors[i]
                if color and len(color) >= 3:  # 确保颜色数据有效
                    channel["c1"] = int(color[0])
                    channel["c2"] = int(color[1])
                    channel["c3"] = int(color[2])
            else:
                channel["c1"] = 255
                channel["c2"] = 255
                channel["c3"] = 255
            
            channel_frame["channels"].append(channel)
        
        return channel_frame, point_frame


    def _build_jsdm_data(self, spreadsheet_data, obj, is_animation=False):
        """构建JSDM数据结构"""
        if is_animation:
            return None
        
        channel_frame,point_frame = self._build_point_frame(spreadsheet_data, 0, 0)

        if not channel_frame or not point_frame:
            return None
        
        plane_count = len(point_frame['points'])

        metadata = self._build_metadata(
            object_name=obj.name,
            is_animation = is_animation,
        )
        

        #构建完整的JSDM数据结构
        jsdm_data = {
            "planeCount": plane_count,
            "name":self.project_name if self.project_name else "Untitled",
            "description": self.description if self.description else "No description", 
            "frameCount": 1,
            "channelFrames": [channel_frame],
            "pointFrames": [point_frame],
            "droneTypes": self._build_drone_types(plane_count),
            "metadata":metadata,
        }
        
        return jsdm_data
    
    def _build_drone_types(self, plane_count):
        """构建无人机类型"""
        if plane_count <= 0:
            return []

        drone_types = []
        for i in range(plane_count):
            cache_data = ["chuniaokj01"]
            try:
                cache_encoded = base64.b64encode(str(cache_data).encode('utf-8')).decode('utf-8')
            except:
                cache_encoded = ""
            
            drone_type = {
                "no":str(i + 1),
                "type":21,
                "cache": cache_encoded,
            }
            drone_types.append(drone_type)

        return drone_types

    def _build_metadata(self,object_name,frame_rate = None, is_animation=False):
        """构建元数据"""
        metadata = {
            "exportTime":time.strftime("%Y-%m-%d %H:%M:%S"),
            "objectName":object_name,
            "blenderVersion":bpy.app.version_string,
            "pluginVersion":"1.1.0",
            "exportSetting":{
                "coordinateSystem": self.coordinate_system,
                "scaleFactor": self.scale_factor,
                "includeColors": self.include_colors,
                "includeIDs": self.include_ids,
                "exportAsAnimation": is_animation,
                "timeUnit":"milliseconds"
            }
        }

        if is_animation and frame_rate:
            # 计算动画总时长
            duration_seconds = (self.frame_end - self.frame_start + 1) / frame_rate
            duration_ms = duration_seconds * 1000

            metadata["animationSettings"]={
                "frameStart": self.frame_start,
                "frameEnd": self.frame_end,
                "frameStep": self.frame_step,
                "frameRate": frame_rate,
                "totalFrames": self.frame_end - self.frame_start + 1,
                "durationSeconds": duration_seconds,
                "durationMilliseconds": duration_ms,
                "timePerFrame": 1000.0 / frame_rate
            }

        return metadata
    
    def draw(self, context):
        """绘制导出设置面板"""
        layout = self.layout
        
        box = layout.box()
        box.label(text="导出设置", icon='EXPORT')

        # 元数据设置
        box.label(text="项目信息", icon='FILE')
        box.prop(self, "project_name")
        box.prop(self, "description")
        
        # 数据设置
        box.label(text="数据设置", icon='MESH_DATA')
        box.prop(self, "include_colors")
        box.prop(self, "include_ids")

        # 动画设置
        box.label(text="动画设置", icon='RENDER_ANIMATION')
        box.prop(self, "export_animation")

        if self.export_animation:
            anim_box = box.box()
            anim_box.prop(self, "frame_start")
            anim_box.prop(self, "frame_end")
            anim_box.prop(self, "frame_step")
            anim_box.label(text=f"帧率：{context.scene.render.fps} FPS",icon = 'PREVIEW_RANGE')
            total_frames = ((self.frame_end - self.frame_start) // self.frame_step) + 1
            anim_box.label(text=f"总帧数：{total_frames}")
            anim_box.label(text=f"时长: {total_frames / context.scene.render.fps:.2f}秒")
        
        # 坐标系设置
        box.label(text="坐标系", icon='WORLD')
        box.prop(self, "coordinate_system")
        box.prop(self, "scale_factor")


class PCJSDM_OT_InspectGeometryNodes(bpy.types.Operator):
    """检查几何节点数据"""
    
    bl_idname = "pc_jsdm.inspect_geometry_nodes"
    bl_label = "检查几何节点数据"
    bl_description = "检查几何节点中的电子表格数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行检查"""
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, "请选择对象")
            return {'CANCELLED'}
        
        from ..util.geometry_nodes_reader import GeometryNodesReader
        reader = GeometryNodesReader(obj)
        
        if not reader.has_geometry_nodes():
            self.report({'WARNING'}, "对象没有几何节点")
            return {'CANCELLED'}
        
        # 获取数据
        data = reader.get_spreadsheet_data()
        metadata = reader.get_metadata()
        
        # 显示信息
        print("\n" + "="*60)
        print("几何节点数据检查")
        print("="*60)
        print(f"对象: {obj.name}")
        print(f"几何节点树: {reader.node_tree.name}")
        print(f"点数量: {len(data.get('positions', []))}")
        print(f"颜色数据: {len(data.get('colors', []))} 个")
        print(f"ID数据: {len(data.get('ids', []))} 个")
        print(f"属性数量: {metadata.get('attribute_count', 0)}")

        #检查动画数据
        print(f"\n动画信息")
        print(f"当前帧：{context.scene.frame_current}")
        print(f"帧范围：{context.scene.frame_start} - {context.scene.frame_end}")
        print(f"帧率：{context.scene.render.fps} FPS")

        #检查不同帧的数据
        original_frame = context.scene.frame_current
        frames_to_check = [original_frame, original_frame +1, original_frame + 5]

        print("\n跨帧数据比较：")
        for frame in frames_to_check:
            context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            
            frame_data = reader.get_spreadsheet_data()
            pos_count = len(frame_data.get('positions', []))
            print(f"帧 {frame}: {pos_count} 个点")

        #恢复原始帧
        context.scene.frame_set(original_frame)
        
        # 显示属性详情
        if metadata.get('attributes'):
            print("\n属性详情:")
            for attr in metadata['attributes']:
                print(f"  {attr['name']}: {attr['data_type']} ({attr['domain']}), {attr['length']} 个")
        
        # 显示前几个点的数据示例
        positions = data.get('positions', [])
        if positions:
            print("\n位置数据示例 (前5个点):")
            for i, pos in enumerate(positions[:5]):
                print(f"  点{i+1}: {pos}")
        
        colors = data.get('colors', [])
        if colors:
            print("\n颜色数据示例 (前5个点):")
            for i, color in enumerate(colors[:5]):
                print(f"  点{i+1}: {color}")
        
        print("="*60)
        
        self.report({'INFO'}, f"检查完成: {len(positions)} 个点")
        return {'FINISHED'}