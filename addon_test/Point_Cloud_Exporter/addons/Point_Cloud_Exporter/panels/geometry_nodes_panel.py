"""
几何节点数据面板
显示几何节点电子表格数据信息
"""

import bpy
from bpy.types import Panel
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order


class BasePanel(object):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "点云导出"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


@reg_order(0)
class PCJSDM_PT_MainPanel(BasePanel, bpy.types.Panel):
    bl_label = "几何节点JSDM导出器"
    bl_idname = "SCENE_PT_jsdm_exporter"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        
        # 状态检查
        obj = context.active_object
        if not obj:
            layout.label(text=i18n("请选择对象"), icon='ERROR')
            return
        
        # 检查几何节点
        from ..util.geometry_nodes_reader import get_spreadsheet_summary
        summary = get_spreadsheet_summary(obj)
        
        if not summary['has_geometry_nodes']:
            layout.label(text=i18n("对象没有几何节点修改器"), icon='INFO')
            return
        
        # 头部信息
        box = layout.box()
        row = box.row()
        row.label(text=f"{i18n('对象:')} {obj.name}", icon='MESH_DATA')
        
        #动画信息
        if context.scene.frame_end > context.scene.frame_start:
            box = layout.box()
            row.label(text = f"{i18n('动画帧范围：')}{context.scene.frame_start} - {context.scene.frame_end}",icon = 'RENDER_ANIMATION')

            row = box.row()
            row.label(text=f"{i18n('动画帧率：')}{context.scene.render.fps} FPS",icon=  'TIME')

        # 导出按钮
        layout.separator()
        col = layout.column()
        col.scale_y = 1.2

        #添加导出设置按钮
        col.operator_context = 'INVOKE_DEFAULT'
        col.operator("pc_export_pointcloud.jsdm", text=i18n("导出JSDM"), icon='EXPORT')


@reg_order(1)
class PCJSDM_PT_GeometryNodesPanel(BasePanel, bpy.types.Panel):
    bl_label = "几何节点数据"
    bl_idname = "SCENE_PT_jsdm_geometry_nodes"
    bl_parent_id = "SCENE_PT_jsdm_exporter"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        """仅在选择了有几何节点的对象时显示"""
        obj = context.active_object
        if not obj:
            return False
        
        from ..util.geometry_nodes_reader import GeometryNodesReader
        reader = GeometryNodesReader(obj)
        return reader.has_geometry_nodes()
    
    def draw(self, context: bpy.types.Context):
        """绘制面板内容"""
        layout = self.layout
        obj = context.active_object
        
        if not obj:
            layout.label(text=i18n("请选择对象"), icon='ERROR')
            return
        
        from ..util.geometry_nodes_reader import GeometryNodesReader, get_spreadsheet_summary
        reader = GeometryNodesReader(obj)
        summary = get_spreadsheet_summary(obj)
        
        if not summary['has_geometry_nodes']:
            layout.label(text=i18n("对象没有几何节点修改器"), icon='INFO')
            return
        
        box = layout.box()
        box.label(text=i18n("几何节点数据"), icon='NODETREE')

        # 基本信息
        col = box.column()
        col.label(text=f"{i18n('几何节点:')} {reader.node_tree.name}", icon='NODE')
        
        #动画测试按钮
        if context.scene.frame_end >context.scene.frame_start:
            col.separator()
            col.label(text = i18n("动画信息："), icon = 'RENDER_ANIMATION')

            text_box = col.box()
            row = text_box.row()
            row.label(text="测试动画数据：")

            row = text_box.row(align=True)
            row.operator("pc_jsdm.inspect_geometry_nodes",text = "检查当前帧", icon = 'VIEWZOOM')

            #添加快速动画测试按钮
            op = row.operator("pc_jsdm.inspect_animation_data",text = "测试动画", icon = 'PLAY')
            op.frame_start = context.scene.frame_start
            op.frame_end = context.scene.frame_end

        
        # 数据统计
        col.separator()
        col.label(text=i18n("数据统计"), icon='LINENUMBERS_ON')
        col.label(text=f"{i18n('点数量:')} {summary['point_count']}")
        col.label(text=f"{i18n('颜色数据:')} {'✓ ' + i18n('有') if summary['has_colors'] else '✗ ' + i18n('无')}")
        col.label(text=f"{i18n('ID数据:')} {'✓ ' + i18n('有') if summary['has_ids'] else '✗ ' + i18n('无')}")
        
        # 属性列表
        if summary['attributes']:
            col.separator()
            col.label(text=i18n("属性列表"), icon='PROPERTIES')
            
            for attr_name in summary['attributes']:
                row = col.row()
                row.label(text=attr_name)
        
        # 操作按钮
        col.separator()
        col.label(text=i18n("数据操作"), icon='TOOL_SETTINGS')
        
        op_col = col.column(align=True)
        op_col.operator("pc_jsdm.inspect_geometry_nodes", text=i18n("检查几何节点数据"), icon='VIEWZOOM')
        
        # 导出建议
        if summary['point_count'] > 0:
            col.separator()
            col.label(text=i18n("导出建议"), icon='INFO')

            if context.scene.frame_end > context.scene.frame_start:
                col.label(text="✓ 检测到动画帧范围", icon='CHECKMARK')
                col.label(text="  可启用动画导出", icon='RIGHTARROW_THIN')

class PCJSDM_OT_InspectAnimationData(bpy.types.Operator):
    """检查动画数据"""
    
    bl_idname = "pc_jsdm.inspect_animation_data"
    bl_label = "测试动画数据"
    bl_description = "检查动画序列中的数据变化"
    bl_options = {'REGISTER', 'UNDO'}
    
    frame_start: bpy.props.IntProperty(default=1)
    frame_end: bpy.props.IntProperty(default=250)
    
    def execute(self, context):
        """执行动画数据检查"""
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, "请选择对象")
            return {'CANCELLED'}
        
        from ..util.geometry_nodes_reader import GeometryNodesReader
        reader = GeometryNodesReader(obj)
        
        if not reader.has_geometry_nodes():
            self.report({'WARNING'}, "对象没有几何节点")
            return {'CANCELLED'}
        
        original_frame = context.scene.frame_current
        frame_step = max(1, (self.frame_end - self.frame_start) // 10)  # 采样10帧
        
        print("\n" + "="*60)
        print("动画数据测试")
        print("="*60)
        print(f"对象: {obj.name}")
        print(f"测试帧范围: {self.frame_start} - {self.frame_end}")
        print(f"帧步长: {frame_step}")
        
        point_counts = []
        has_color_changes = False
        has_position_changes = False
        
        # 获取第一帧数据作为参考
        context.scene.frame_set(self.frame_start)
        bpy.context.view_layer.update()
        first_frame_data = reader.get_spreadsheet_data()
        first_positions = first_frame_data.get('positions', [])
        first_colors = first_frame_data.get('colors', [])
        
        # 检查多帧数据
        for frame in range(self.frame_start, self.frame_end + 1, frame_step):
            context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            
            frame_data = reader.get_spreadsheet_data()
            positions = frame_data.get('positions', [])
            colors = frame_data.get('colors', [])
            
            point_counts.append(len(positions))
            
            # 检查数据变化
            if frame > self.frame_start:
                if len(positions) != len(first_positions):
                    has_position_changes = True
                
                if colors and first_colors:
                    if len(colors) != len(first_colors):
                        has_color_changes = True
                    else:
                        # 比较颜色值
                        for i in range(min(5, len(colors))):  # 只比较前5个
                            if colors[i] != first_colors[i]:
                                has_color_changes = True
                                break
            
            print(f"  帧 {frame:4d}: {len(positions):6d} 个点")
        
        # 恢复原始帧
        context.scene.frame_set(original_frame)
        
        # 分析结果
        print("\n动画分析结果:")
        print(f"  点数量范围: {min(point_counts)} - {max(point_counts)}")
        print(f"  点数量变化: {'有' if min(point_counts) != max(point_counts) else '无'}")
        print(f"  位置变化: {'有' if has_position_changes else '无'}")
        print(f"  颜色变化: {'有' if has_color_changes else '无'}")
        
        if has_position_changes or has_color_changes:
            print(f"  ✅ 检测到动画变化，适合导出动画")
        else:
            print(f"  ⚠️ 未检测到变化，可能不需要导出动画")
        
        print("="*60)
        
        self.report({'INFO'}, f"动画测试完成: {len(point_counts)} 个采样帧")
        return {'FINISHED'}

def menu_func_export(self, context):
    """添加到文件菜单"""
    from ....common.i18n.i18n import i18n
    self.layout.operator("pc_export_pointcloud_jsdm", text=i18n("JSDM (.jsdm)"), icon='EXPORT')