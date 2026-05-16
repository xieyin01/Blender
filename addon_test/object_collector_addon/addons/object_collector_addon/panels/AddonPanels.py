import bpy
from bpy.types import Context
import typing
from typing import List, Tuple, Optional, Any


from ..config import __addon_name__
from ..operators.AddonOperators import (
    CollectObjectOperator,
    RemoveCollectedObjectOperator,
    SelectAllCollectedOperator
)

from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order

class VIEW3D_UL_object_collector(bpy.types.UIList ):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index = 0, flt_flag = 0):
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.object_pointer,"name",text = "name",emboss=False,icon_value=icon)
            layout.prop(item.object_pointer,"obj_description",emboss=False, text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
    
    # 过滤属性
    filter_name: bpy.props.StringProperty(
        name="Filter",
        default="",
        update=lambda self, context: self._on_filter_update(context),
        options={'TEXTEDIT_UPDATE'}
    )  # type: ignore
    
    def _on_filter_update(self, context):
        """过滤更新时，保存到场景属性"""
        # 场景已经有 collection_filter 属性（通过框架添加）
        context.scene.collection_filter = self.filter_name
    
    def filter_items(self, context, data, property):
        """过滤列表项"""
        
        # 获取数据项
        items = getattr(data, property, [])
        
        # 如果不需要过滤，返回所有项
        if not hasattr(self, 'filter_name') or not self.filter_name:
            filtered_flags = [self.bitflag_filter_item] * len(items)
            ordered = list(range(len(items)))
            return filtered_flags, ordered
        
        # 导入过滤函数
        try:
            from ..util.util import filter_collected_items
            filter_func_available = True
        except ImportError:
            filter_func_available = False
        
        if filter_func_available:
            # 使用高级过滤函数
            filtered_items, filtered_indices = filter_collected_items(
                items=items,
                filter_name=self.filter_name,
                search_fields=['name', 'obj_description'],  # 搜索名称和描述字段
                case_sensitive=False,
                use_regex=False,
                match_mode='smart',
                enable_cache=True,
                batch_size=100
            )
        else:
            # 备用过滤函数
            filter_lower = self.filter_name.lower()
            filtered_indices = []
            
            for idx, item in enumerate(items):
                show = False
                
                # 检查对象名称
                if hasattr(item, 'object_pointer') and item.object_pointer:
                    obj = item.object_pointer
                    
                    # 检查对象名称
                    if hasattr(obj, 'name') and filter_lower in obj.name.lower():
                        show = True
                    
                    # 检查对象类型
                    if not show and hasattr(obj, 'type'):
                        obj_type = obj.type.lower()
                        if filter_lower in obj_type:
                            show = True
                
                # 检查自定义描述字段
                if not show and hasattr(item, 'obj_description'):
                    desc = getattr(item, 'obj_description', '')
                    if isinstance(desc, str) and filter_lower in desc.lower():
                        show = True
                
                # 检查项目名称（如果有）
                if not show and hasattr(item, 'name'):
                    item_name = getattr(item, 'name', '')
                    if isinstance(item_name, str) and filter_lower in item_name.lower():
                        show = True
                
                if show:
                    filtered_indices.append(idx)
        
        # 创建过滤标志位列表
        filtered_flags = []
        for i in range(len(items)):
            if i in filtered_indices:
                filtered_flags.append(self.bitflag_filter_item)  # 显示
            else:
                filtered_flags.append(0)  # 隐藏
        
        # 保持原顺序（UIList需要返回排序列表）
        ordered = list(range(len(items)))
        
        return filtered_flags, ordered

class BasePanel(object):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ExampleAddon"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


@reg_order(0)
class ExampleAddonPanel(BasePanel, bpy.types.Panel):
    bl_label = "Example Addon Side Bar Panel"
    bl_idname = "SCENE_PT_sample"

    def draw(self, context: bpy.types.Context):
        
        layout = self.layout

        row = layout.row()
        row.template_list("VIEW3D_UL_object_collector","",context.scene,"collected_objects",context.scene,"current_object_index")

        col=row.column(align=True)
        col.operator(CollectObjectOperator.bl_idname,icon="ADD",text="")
        col.operator(RemoveCollectedObjectOperator.bl_idname,icon="REMOVE",text="")

        row = layout.row()
        row.operator(CollectObjectOperator.bl_idname)
        row.operator(SelectAllCollectedOperator.bl_idname)
        row.operator(RemoveCollectedObjectOperator.bl_idname)
        
        if context.scene.current_object_index >= 0:
            layout.prop(context.scene.collected_objects[context.scene.current_object_index].object_pointer,"obj_description")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True
