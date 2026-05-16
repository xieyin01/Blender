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
    
    def filter_items(self, context: Optional['Context'], 
                     data: Any, 
                     property: str)-> Tuple[List[int], List[int]]:
        items = getattr(data, property, [])
    
        # 空过滤：显示所有
        if not self.filter_name:
            return [self.bitflag_filter_item] * len(items), list(range(len(items)))
        
        filter_lower = self.filter_name.lower()
        filtered = []
        
        for item in items:
            obj = getattr(item, 'object_pointer', None)
            show_item = False
            
            if obj:
                # 检查名称
                if hasattr(obj, 'name') and filter_lower in obj.name.lower():
                    show_item = True
                
                # 检查描述
                if not show_item and hasattr(obj, 'obj_description'):
                    desc = getattr(obj, 'obj_description', '')
                    if filter_lower in desc.lower():
                        show_item = True
            
            filtered.append(self.bitflag_filter_item if show_item else 0)
        
        # 保持原顺序
        ordered = list(range(len(items)))
        
        return filtered, ordered

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
