"""
导出面板
提供JSDM导出的UI界面
"""

import bpy
from bpy.types import Panel, Menu
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
    bl_label = "点云JSDM导出器"
    bl_idname = "SCENE_PT_jsdm_exporter"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        settings = scene.pc_jsdm_export_settings
        
        # 状态检查
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            layout.label(text=i18n("请选择网格对象"), icon='ERROR')
            return
        
        # 头部信息
        box = layout.box()
        row = box.row()
        row.label(text=f"{i18n('对象:')} {obj.name}", icon='MESH_DATA')
        
        row = box.row()
        row.label(text=f"{i18n('顶点数:')} {len(obj.data.vertices)}")
        
        if obj.animation_data and obj.animation_data.action:
            row = box.row()
            row.label(text=f"{i18n('动画:')} {obj.animation_data.action.name}", icon='ANIM')
        
        # 导出按钮
        layout.separator()
        col = layout.column()
        col.scale_y = 1.2
        col.operator("pc_jsdm.export", text=i18n("导出JSDM"), icon='EXPORT')
        
        # 动画操作按钮
        layout.separator()
        box = layout.box()
        box.label(text=i18n("动画处理"), icon='ANIM')
        
        col = box.column(align=True)
        col.operator("pc_jsdm.extract_animation", text=i18n("提取动画"), icon='IMPORT')
        col.operator("pc_jsdm.bake_animation", text=i18n("烘焙动画"), icon='KEY_HLT')
        col.operator("pc_jsdm.optimize_animation", text=i18n("优化动画"), icon='MODIFIER')


@reg_order(1)
class PCJSDM_PT_ExportSettingsPanel(BasePanel, bpy.types.Panel):
    bl_label = "导出设置"
    bl_idname = "SCENE_PT_jsdm_export_settings"
    bl_parent_id = "SCENE_PT_jsdm_exporter"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        settings = scene.pc_jsdm_export_settings
        
        box = layout.box()
        box.label(text=i18n("导出设置"), icon='SETTINGS')
        
        # 文件设置
        col = box.column(align=True)
        col.prop(settings, "export_path", text=i18n("文件路径"))
        
        # 动画设置
        col.separator()
        col.label(text=i18n("动画设置"), icon='ANIM')
        col.prop(settings, "animation_mode", text="")
        
        row = col.row(align=True)
        row.prop(settings, "start_frame", text=i18n("起始"))
        row.prop(settings, "end_frame", text=i18n("结束"))
        row.prop(settings, "frame_step", text=i18n("步长"))
        
        # 数据设置
        col.separator()
        col.label(text=i18n("数据设置"), icon='MESH_DATA')
        col.prop(settings, "include_colors")
        
        if settings.include_colors:
            col.prop(settings, "color_mode", text="")
        
        col.prop(settings, "include_ids")
        
        # 坐标系设置
        col.separator()
        col.label(text=i18n("坐标系"), icon='WORLD')
        col.prop(settings, "coordinate_system", text="")
        col.prop(settings, "scale_factor")
        
        # 优化设置
        col.separator()
        col.label(text=i18n("优化"), icon='MODIFIER')
        col.prop(settings, "optimize_animation")
        
        if settings.optimize_animation:
            sub = col.column()
            sub.enabled = settings.optimize_animation
            sub.prop(settings, "remove_duplicate_frames")
            sub.prop(settings, "simplify_keyframes")
            
            if settings.simplify_keyframes:
                sub.prop(settings, "simplify_threshold")
        
        # 性能设置
        col.separator()
        col.label(text=i18n("性能"), icon='PREFERENCES')
        col.prop(settings, "use_performance_optimizer")
        
        if settings.use_performance_optimizer:
            sub = col.column()
            sub.enabled = settings.use_performance_optimizer
            sub.prop(settings, "batch_size")
            sub.prop(settings, "enable_cache")
        
        # 调试设置
        col.separator()
        col.label(text=i18n("调试"), icon='CONSOLE')
        col.prop(settings, "debug_mode")
        col.prop(settings, "verbose_logging")


@reg_order(2)
class PCJSDM_PT_AnimationSettingsPanel(BasePanel, bpy.types.Panel):
    bl_label = "动画设置"
    bl_idname = "SCENE_PT_jsdm_animation_settings"
    bl_parent_id = "SCENE_PT_jsdm_exporter"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        settings = scene.pc_jsdm_animation_settings
        
        box = layout.box()
        box.label(text=i18n("动画设置"), icon='SETTINGS')
        
        # 提取设置
        col = box.column(align=True)
        col.label(text=i18n("提取设置"), icon='IMPORT')
        col.prop(settings, "extract_animation_mode", text=i18n("模式"))
        col.prop(settings, "extract_frame_step", text=i18n("帧步长"))
        col.prop(settings, "extract_include_colors", text=i18n("包含颜色"))
        
        # 烘焙设置
        col.separator()
        col.label(text=i18n("烘焙设置"), icon='KEY_HLT')
        col.prop(settings, "bake_location", text=i18n("位置"))
        col.prop(settings, "bake_rotation", text=i18n("旋转"))
        col.prop(settings, "bake_scale", text=i18n("缩放"))
        
        row = col.row()
        row.prop(settings, "bake_simplify_keyframes", text=i18n("简化关键帧"))
        if settings.bake_simplify_keyframes:
            col.prop(settings, "bake_simplify_threshold", text=i18n("阈值"))
        
        # 优化设置
        col.separator()
        col.label(text=i18n("优化设置"), icon='MODIFIER')
        col.prop(settings, "optimize_remove_duplicates", text=i18n("移除重复"))
        col.prop(settings, "optimize_interpolate_missing", text=i18n("插值缺失"))
        
        if settings.optimize_interpolate_missing:
            col.prop(settings, "optimize_max_gap_frames", text=i18n("最大间隔"))


class PCJSDM_MT_ExportMenu(Menu):
    """JSDM导出菜单"""
    
    bl_idname = "PCJSDM_MT_ExportMenu"
    bl_label = "JSDM导出"
    
    def draw(self, context):
        """绘制菜单"""
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        
        layout.operator("pc_jsdm.export", text=i18n("导出JSDM..."), icon='EXPORT')
        layout.separator()
        layout.operator("pc_jsdm.extract_animation", text=i18n("提取动画"), icon='IMPORT')
        layout.operator("pc_jsdm.bake_animation", text=i18n("烘焙动画"), icon='KEY_HLT')
        layout.operator("pc_jsdm.optimize_animation", text=i18n("优化动画"), icon='MODIFIER')


def menu_func_export(self, context):
    """添加到文件菜单"""
    from ....common.i18n.i18n import i18n
    self.layout.operator("pc_jsdm.export", text=i18n("JSDM (.jsdm)"), icon='EXPORT')