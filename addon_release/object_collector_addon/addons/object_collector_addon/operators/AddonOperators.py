import bpy

from ..config import __addon_name__
from ..preference.AddonPreferences import ExampleAddonPreferences


# This Example Operator will scale up the selected object
class CollectObjectOperator(bpy.types.Operator):
    '''ExampleAddon'''
    bl_idname = "object.example_ops"
    bl_label = "Collect Object"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        collected_objects = context.selected_objects
        for obj in collected_objects:
            if not obj.has_collected:
                new_obj_pointer = context.scene.collected_objects.add()
                new_obj_pointer.object_pointer = obj
                obj.has_collected = True
        return {'FINISHED'}

class SelectAllCollectedOperator(bpy.types.Operator):
    "Select all collected objects in the list"

    bl_idname = "object.select_all_collected"
    bl_label = "Select All Collected"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.selected_objects.clear()
        for obj in context.scene.collected_objects:
            obj.object_pointer.select_set(True)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len(context.scene.collected_objects) > 0
    
class RemoveCollectedObjectOperator(bpy.types.Operator):

    bl_idname = "object.remove_collected_object"
    bl_label = "Remove Collected Object"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collected_objects = context.scene.collected_objects
        collected_objects[context.scene.current_object_index].object_pointer.has_collected = False
        collected_objects.remove(context.scene.current_object_index)
        context.scene.current_object_index = len(collected_objects) - 1
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.current_object_index >= 0
