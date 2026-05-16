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

    # 添加过滤选项
    use_filter: bpy.props.BoolProperty(
        name="Use Filter",
        description="Apply current filter to selection",
        default=True
    )#type: ignore
    
    def _get_current_filter(self, context):
        """获取当前过滤条件"""
        filter_text = ""
        
        # 从场景属性获取
        if hasattr(context.scene, 'collection_filter'):
            filter_text = context.scene.collection_filter
        
        return filter_text.strip()
    
    def _import_filter_function(self):
        """导入过滤函数"""
        try:
            # 尝试相对导入
            from ..util.util import filter_collected_items
            return filter_collected_items
        except ImportError as e:
            self.report({'ERROR'}, f"无法导入过滤函数: {str(e)}")
            return None
    
    def execute(self, context):
        """执行选择操作"""
        
        # 获取当前过滤条件
        filter_text = ""
        if self.use_filter:
            filter_text = self._get_current_filter(context)
        
        # 导入过滤函数
        filter_func = self._import_filter_function()
        if filter_func is None:
            return {'CANCELLED'}
        
        # 获取收集的对象列表
        try:
            collected_items = context.scene.collected_objects
        except AttributeError:
            self.report({'ERROR'}, "未找到收集的对象列表")
            return {'CANCELLED'}
        
        # 应用过滤
        try:
            filtered_items, filtered_indices = filter_func(
                items=collected_items,
                filter_name=filter_text,
                search_fields=['name', 'obj_description'],  # 搜索名称和描述字段
                case_sensitive=False,
                use_regex=False,
                match_mode='smart',
                enable_cache=True,
                batch_size=500
            )
        except Exception as e:
            self.report({'ERROR'}, f"过滤时出错: {str(e)}")
            return {'CANCELLED'}
        
        if not filtered_items:
            self.report({'WARNING'}, "没有找到匹配的对象")
            return {'CANCELLED'}
        
        # 记录当前选择的原始数量
        original_selected = sum(obj.select_get() for obj in context.scene.objects)
        
        # 清空当前选择（先取消选择所有）
        bpy.ops.object.select_all(action='DESELECT')
        
        # 选择过滤后的对象
        selected_count = 0
        for item in filtered_items:
            # 获取对象指针
            obj = None
            if hasattr(item, 'object_pointer') and item.object_pointer:
                obj = item.object_pointer
            elif hasattr(item, 'object') and item.object:
                obj = item.object
            elif hasattr(item, 'obj') and item.obj:
                obj = item.obj
            elif isinstance(item, bpy.types.Object):
                obj = item
            
            if obj and hasattr(obj, 'select_set'):
                obj.select_set(True)
                selected_count += 1
        
        # 设置活动对象（如果至少选择了一个对象）
        if selected_count > 0:
            # 尝试使用第一个选中的对象作为活动对象
            for item in filtered_items:
                if hasattr(item, 'object_pointer') and item.object_pointer:
                    context.view_layer.objects.active = item.object_pointer
                    break
        
        # 用户反馈
        if filter_text:
            self.report({'INFO'}, f"选择了 {selected_count} 个对象 (过滤: '{filter_text}')")
        else:
            self.report({'INFO'}, f"选择了 {selected_count} 个对象")
        
        # 刷新视图
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        """检查是否可以执行操作"""
        # 确保有收集的对象属性
        if not hasattr(context.scene, 'collected_objects'):
            return False
        
        # 确保收集的对象列表不为空
        try:
            return len(context.scene.collected_objects) > 0
        except:
            return False
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
