import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
import random

try:
    from .. import _selection_history
except ImportError:
    # 如果无法导入，创建空列表
    _selection_history = []

class CollectObjectOperator(bpy.types.Operator):
    """收集物体到集合（按选择顺序）"""
    
    bl_idname = "object.collect_objects"
    bl_label = "收集物体"
    bl_description = "将选中的物体按选择顺序添加到当前集合"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.selected_objects and len(context.selected_objects) > 0

    def execute(self, context: bpy.types.Context):
        selected_objects = context.selected_objects
        
        # 检查是否有集合
        if not hasattr(context.scene, 'collection_sets') or len(context.scene.collection_sets) == 0:
            # 创建默认集合
            new_collection = context.scene.collection_sets.add()
            new_collection.name = "默认集合"
            context.scene.active_collection_index = 0
        
        # 添加到当前集合
        if context.scene.active_collection_index >= 0:
            collection = context.scene.collection_sets[context.scene.active_collection_index]
            
            # 按选择历史记录的顺序添加物体
            ordered_objects = []
            
            # 使用选择历史记录
            if _selection_history:
                for obj in _selection_history:
                    if obj in selected_objects and obj not in ordered_objects:
                        ordered_objects.append(obj)
            
            # 如果没有选择历史，使用当前选中的顺序
            if not ordered_objects:
                ordered_objects = selected_objects
            
            added_count = 0
            for obj in ordered_objects:
                if collection.add_object(obj, context):
                    added_count += 1
            
            if added_count > 0:
                self.report({'INFO'}, f"已按选择顺序添加 {added_count} 个物体到集合 '{collection.name}'")
            else:
                self.report({'WARNING'}, "没有新物体被添加")
        else:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        # 清理选择历史
        if _selection_history:
            _selection_history.clear()
        
        return {'FINISHED'}

class AddCollectionDirectOperator(bpy.types.Operator):
    """直接添加新集合，无确认对话框"""
    
    bl_idname = "object.add_collection_direct"
    bl_label = "添加集合"
    bl_description = "直接添加一个新集合"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 创建新集合
        collection_sets = getattr(context.scene, 'collection_sets', None)
        if collection_sets is None:
            self.report({'ERROR'}, "集合系统未初始化")
            return {'CANCELLED'}
        
        new_collection = collection_sets.add()
        
        # 生成默认名称
        collection_count = len(collection_sets)
        new_collection.name = f"集合_{collection_count}"
        
        # 设置默认颜色
        colors = [
            (0.2, 0.6, 1.0),   # 蓝色
            (0.8, 0.3, 0.3),   # 红色
            (0.3, 0.8, 0.3),   # 绿色
            (0.9, 0.7, 0.1),   # 黄色
            (0.7, 0.3, 0.9),   # 紫色
        ]
        new_collection.color_tag = colors[(collection_count - 1) % len(colors)]
        
        # 设置为当前活动集合
        context.scene.active_collection_index = len(collection_sets) - 1
        
        self.report({'INFO'}, f"已添加集合: {new_collection.name}")
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return True

class RemoveCollectionOperator(bpy.types.Operator):
    """删除当前集合"""
    
    bl_idname = "object.remove_collection"
    bl_label = "删除集合"
    bl_description = "删除当前选中的集合"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection_name = context.scene.collection_sets[context.scene.active_collection_index].name
        
        # 删除集合
        context.scene.collection_sets.remove(context.scene.active_collection_index)
        
        # 调整活动索引
        if context.scene.active_collection_index >= len(context.scene.collection_sets):
            context.scene.active_collection_index = len(context.scene.collection_sets) - 1
        
        self.report({'INFO'}, f"已删除集合: {collection_name}")
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context.scene, 'collection_sets') and 
                len(context.scene.collection_sets) > 0 and
                context.scene.active_collection_index >= 0)

class RenameCollectionDirectOperator(bpy.types.Operator):
    """直接重命名集合，无确认对话框"""
    
    bl_idname = "object.rename_collection_direct"
    bl_label = "重命名集合"
    bl_description = "直接重命名当前集合"
    bl_options = {'REGISTER', 'UNDO'}
    
    new_name: bpy.props.StringProperty(
        name="新名称",
        description="集合的新名称",
        default=""
    )
    
    def execute(self, context):
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        old_name = collection.name
        
        if not self.new_name.strip():
            # 如果名称为空，使用默认名称
            self.new_name = f"集合_{context.scene.active_collection_index + 1}"
        
        collection.name = self.new_name
        self.report({'INFO'}, f"已将集合重命名为 '{self.new_name}'")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # 直接执行，不弹出对话框
        if context.scene.active_collection_index >= 0:
            collection = context.scene.collection_sets[context.scene.active_collection_index]
            self.new_name = collection.name
        return self.execute(context)
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context.scene, 'collection_sets') and 
                len(context.scene.collection_sets) > 0 and
                context.scene.active_collection_index >= 0)

class SelectAllCollectedOperator(bpy.types.Operator):
    """选择当前集合中的所有物体（支持过滤）"""
    
    bl_idname = "object.select_all_collected"
    bl_label = "选择集合物体"
    bl_description = "选择当前集合中的所有物体，支持过滤"
    bl_options = {'REGISTER', 'UNDO'}

    # 添加过滤选项
    use_filter: bpy.props.BoolProperty(
        name="Use Filter",
        description="在选择时应用当前过滤条件",
        default=True
    )
    
    def _get_current_filter(self, context):
        """获取当前过滤条件"""
        filter_text = ""
        if (context.scene.active_collection_index >= 0 and 
            hasattr(context.scene, 'collection_sets') and 
            len(context.scene.collection_sets) > context.scene.active_collection_index):
            
            collection = context.scene.collection_sets[context.scene.active_collection_index]
            if hasattr(collection, 'filter_name'):
                filter_text = collection.filter_name
        return filter_text.strip()
    
    def _import_filter_function(self):
        """导入过滤函数"""
        try:
            from ..util.util import filter_collected_items
            return filter_collected_items
        except ImportError as e:
            self.report({'ERROR'}, f"无法导入过滤函数: {str(e)}")
            return None
    
    def execute(self, context):
        # 检查当前集合
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        # 获取当前过滤条件
        filter_text = ""
        if self.use_filter:
            filter_text = self._get_current_filter(context)
        
        # 获取集合中的物体列表
        items = collection.items
        
        if not items:
            self.report({'WARNING'}, "集合中没有物体")
            return {'CANCELLED'}
        
        # 导入过滤函数
        filter_func = self._import_filter_function()
        if filter_func is None:
            return {'CANCELLED'}
        
        # 应用过滤（使用缓存的搜索文本）
        try:
            filtered_items, filtered_indices = filter_func(
                items=items,
                filter_name=filter_text,
                search_fields=['name', 'obj_description'],
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
            self.report({'WARNING'}, "没有找到匹配的物体")
            return {'CANCELLED'}
        
        # 清空当前选择
        bpy.ops.object.select_all(action='DESELECT')
        
        # 选择过滤后的物体
        selected_count = 0
        skipped_not_in_view = 0
        skipped_hidden = 0
        
        for item in filtered_items:
            if not hasattr(item, 'object_pointer') or not item.object_pointer:
                continue
                
            obj = item.object_pointer
            
            # 检查物体是否在视图层中
            if obj.name not in context.view_layer.objects:
                skipped_not_in_view += 1
                continue
            
            # 检查物体是否被隐藏
            if obj.hide_get():
                skipped_hidden += 1
                continue
            
            # 选中物体
            try:
                obj.select_set(True)
                selected_count += 1
            except RuntimeError:
                skipped_not_in_view += 1
                continue
        
        # 设置活动物体
        if selected_count > 0:
            for item in filtered_items:
                if hasattr(item, 'object_pointer') and item.object_pointer:
                    obj = item.object_pointer
                    if obj.name in context.view_layer.objects and obj.select_get():
                        context.view_layer.objects.active = obj
                        break
        
        # 用户反馈
        messages = []
        if selected_count > 0:
            messages.append(f"选择了 {selected_count} 个物体")
        
        if skipped_not_in_view > 0:
            messages.append(f"{skipped_not_in_view} 个物体不在当前视图层")
        
        if skipped_hidden > 0:
            messages.append(f"{skipped_hidden} 个物体被隐藏")
        
        if filter_text:
            messages.append(f"过滤: '{filter_text}'")
        
        if messages:
            self.report({'INFO'}, "，".join(messages))
        
        # 刷新视图
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context.scene, 'collection_sets') and 
                len(context.scene.collection_sets) > 0 and
                context.scene.active_collection_index >= 0)

class RemoveCollectedObjectOperator(bpy.types.Operator):
    """从当前集合移除选中的物体"""
    
    bl_idname = "object.remove_collected_object"
    bl_label = "从集合移除"
    bl_description = "从当前集合中移除选中的物体"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 检查当前集合
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        # 检查是否有可移除的物体
        has_ui_selected = (collection.active_item_index >= 0 and 
                          collection.active_item_index < len(collection.items))
        
        # 获取当前集合的所有物体指针（用于快速查找）
        collection_objects = [item.object_pointer for item in collection.items if item.object_pointer]
        
        # 检查场景中选中的物体是否在当前集合中
        scene_selected_in_collection = []
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj in collection_objects:
                    scene_selected_in_collection.append(obj)
        
        # 如果没有可移除的物体，返回错误
        if not has_ui_selected and not scene_selected_in_collection:
            self.report({'ERROR'}, "没有选中的集合项或场景物体不在当前集合中")
            return {'CANCELLED'}
        
        removed_count = 0
        removed_names = []
        
        # 情况1：从UI列表选中的物体
        if has_ui_selected:
            item_to_remove = collection.items[collection.active_item_index]
            if item_to_remove.object_pointer:
                obj_name = item_to_remove.object_pointer.name
                # 记录添加顺序信息
                add_sequence = getattr(item_to_remove, 'add_sequence', 0)
                
                # 移除选中的项
                collection.items.remove(collection.active_item_index)
                removed_count += 1
                removed_names.append(obj_name)
                
                # 修改这里：移除后不自动选中下一个物体，而是取消选中
                collection.active_item_index = -1
                
                self.report({'INFO'}, f"已移除物体 '{obj_name}' (添加序号: {add_sequence})")
        
        # 情况2：从场景选中的物体（移除所有在集合中的选中物体）
        if scene_selected_in_collection:
            # 需要从后往前移除，避免索引变化
            indices_to_remove = []
            for obj in scene_selected_in_collection:
                # 查找该物体在集合中的索引
                for i, item in enumerate(collection.items):
                    if item.object_pointer == obj:
                        indices_to_remove.append(i)
                        break
            
            # 按降序排序，从后往前移除
            indices_to_remove.sort(reverse=True)
            for index in indices_to_remove:
                item_to_remove = collection.items[index]
                if item_to_remove.object_pointer:
                    obj_name = item_to_remove.object_pointer.name
                    add_sequence = getattr(item_to_remove, 'add_sequence', 0)
                    
                    # 移除项
                    collection.items.remove(index)
                    removed_count += 1
                    removed_names.append(obj_name)
                    
                    # 修改这里：如果移除的是当前UI选中的项，将选中索引设为-1
                    if collection.active_item_index == index:
                        collection.active_item_index = -1
                    elif collection.active_item_index > index:
                        # 如果UI选中索引在当前移除索引之后，需要递减
                        collection.active_item_index -= 1
            
            if scene_selected_in_collection:
                self.report({'INFO'}, f"已移除 {len(scene_selected_in_collection)} 个场景选中物体")
        
        # 重新计算所有项的order_index（显示顺序）
        for i, item in enumerate(collection.items):
            item.order_index = i
        
        # 汇总反馈信息
        if removed_count > 0:
            if len(removed_names) <= 3:  # 只显示前几个物体名称
                names_str = ", ".join(removed_names[:3])
                if len(removed_names) > 3:
                    names_str += f" 等 {removed_count} 个物体"
            else:
                names_str = f"{removed_count} 个物体"
            
            self.report({'INFO'}, f"已从集合 '{collection.name}' 移除 {names_str}")
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """检查是否可以执行操作"""
        # 基本条件检查
        if not hasattr(context.scene, 'collection_sets') or len(context.scene.collection_sets) == 0:
            return False
        
        if context.scene.active_collection_index < 0:
            return False
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        # 条件1：集合UI列表中有选中的项
        has_ui_selected = (collection.active_item_index >= 0 and 
                          collection.active_item_index < len(collection.items))
        
        # 条件2：场景中选中的物体在当前集合中
        has_scene_selected_in_collection = False
        if context.selected_objects:
            # 获取当前集合的所有物体指针
            collection_objects = [item.object_pointer for item in collection.items if item.object_pointer]
            # 检查场景中选中的物体是否在集合中
            for obj in context.selected_objects:
                if obj in collection_objects:
                    has_scene_selected_in_collection = True
                    break
        
        # 只要满足任一条件即可激活按钮
        return has_ui_selected or has_scene_selected_in_collection

class SelectCollectionByClickOperator(bpy.types.Operator):
    """通过点击集合名称选择集合内物体"""
    
    bl_idname = "object.select_collection_by_click"
    bl_label = "选择集合物体"
    bl_description = "点击集合名称自动选择该集合内所有物体"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 接收集合索引参数
    collection_index: bpy.props.IntProperty(
        name="Collection Index",
        default=0,
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        # 1. 设置当前活动集合索引
        context.scene.active_collection_index = self.collection_index
        
        # 2. 获取目标集合
        if self.collection_index < 0 or self.collection_index >= len(context.scene.collection_sets):
            self.report({'ERROR'}, "无效的集合索引")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[self.collection_index]
        
        # 3. 清空当前选择
        bpy.ops.object.select_all(action='DESELECT')
        
        # 4. 选择集合内所有物体
        selected_count = 0
        for item in collection.items:
            if hasattr(item, 'object_pointer') and item.object_pointer:
                obj = item.object_pointer
                
                # 检查物体是否在当前视图层
                if obj.name not in context.view_layer.objects:
                    continue
                
                # 检查物体是否被隐藏
                if obj.hide_get():
                    continue
                
                # 选中物体
                try:
                    obj.select_set(True)
                    selected_count += 1
                except Exception:
                    continue
        
        # 5. 设置活动物体
        if selected_count > 0:
            for item in collection.items:
                if hasattr(item, 'object_pointer') and item.object_pointer:
                    obj = item.object_pointer
                    if obj.select_get():
                        context.view_layer.objects.active = obj
                        break
        
        # 6. 反馈信息
        if selected_count > 0:
            self.report({'INFO'}, f"已选择集合 '{collection.name}' 中的 {selected_count} 个物体")
        else:
            self.report({'WARNING'}, f"集合 '{collection.name}' 中没有可选的物体")
        
        # 7. 刷新界面
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, 'collection_sets') and len(context.scene.collection_sets) > 0

class ViewAddSequenceOperator(bpy.types.Operator):
    """查看物体顺序信息"""
    
    bl_idname = "object.view_add_sequence"
    bl_label = "查看顺序"
    bl_description = "查看集合中物体的顺序信息（默认按自定义顺序）"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        """直接执行，无需对话框"""
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        if not collection.items:
            self.report({'WARNING'}, "集合中没有物体")
            return {'CANCELLED'}
        
        # 默认按自定义顺序（order_index）排序
        sorted_items = sorted(collection.items, key=lambda x: x.order_index)
        
        # 显示在信息栏
        self.report({'INFO'}, f"=== 集合 '{collection.name}' 物体顺序（自定义顺序）===")
        
        for i, item in enumerate(sorted_items, 1):
            if item.object_pointer:
                obj_name = item.object_pointer.name
                order_index = item.order_index
                add_sequence = getattr(item, 'add_sequence', 0)
                
                # 构建显示信息
                info = f"{i:3d}. {obj_name} [位:{order_index+1}"
                
                # 如果添加序号与当前位置不同，显示添加序号
                if add_sequence != order_index + 1:
                    info += f" | 添:{add_sequence:03d}"
                
                # 显示添加帧数
                added_frame = getattr(item, 'added_frame', 0)
                if added_frame > 0:
                    info += f" | 帧:{added_frame}"
                
                # 显示obj_description（如果有）
                if hasattr(item.object_pointer, 'obj_description') and item.object_pointer.obj_description:
                    desc = item.object_pointer.obj_description
                    if len(desc) > 15:
                        desc = desc[:15] + "..."
                    info += f" | '{desc}'"
                
                info += "]"
                
                self.report({'INFO'}, info)
        
        self.report({'INFO'}, f"共 {len(sorted_items)} 个物体")
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context.scene, 'collection_sets') and 
                len(context.scene.collection_sets) > 0 and
                context.scene.active_collection_index >= 0)

class SetCustomOrderOperator(bpy.types.Operator):
    """按选择顺序设置排列顺序"""
    
    bl_idname = "object.set_custom_order"
    bl_label = "设置排列顺序"
    bl_description = "按照选择顺序设置集合中物体的排列顺序"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        if not collection.items:
            self.report({'WARNING'}, "集合中没有物体")
            return {'CANCELLED'}
        
        # 获取当前集合中的物体
        collection_objects = [item.object_pointer for item in collection.items if item.object_pointer]
        
        if not collection_objects:
            self.report({'WARNING'}, "集合中没有有效物体")
            return {'CANCELLED'}
        
        # 使用选择历史记录的顺序
        ordered_objects = []
        
        # 从选择历史中提取在当前集合中的物体，保持选择历史中的顺序
        for obj in _selection_history:
            if obj and obj in collection_objects and obj not in ordered_objects:
                ordered_objects.append(obj)
        
        # 如果没有选择历史或为空，使用当前选中的物体
        if not ordered_objects:
            # 按物体名称排序作为备选
            ordered_objects = sorted(
                [obj for obj in collection_objects if obj.select_get()],
                key=lambda x: x.name
            )
            
            # 如果没有选中的物体，使用所有物体按名称排序
            if not ordered_objects:
                ordered_objects = sorted(collection_objects, key=lambda x: x.name)
        
        # 创建物体到集合项的映射
        item_dict = {}
        for item in collection.items:
            if item.object_pointer:
                item_dict[item.object_pointer] = item
        
        # 按照ordered_objects的顺序设置新的order_index
        new_order = 0
        
        # 处理ordered_objects中的物体（按选择顺序）
        for obj in ordered_objects:
            if obj in item_dict:
                item = item_dict[obj]
                item.order_index = new_order
                new_order += 1
        
        # 处理剩下的物体（保持原来的相对顺序）
        remaining_objects = [obj for obj in collection_objects if obj not in ordered_objects]
        
        # 按原来的order_index排序
        remaining_items = []
        for obj in remaining_objects:
            if obj in item_dict:
                remaining_items.append(item_dict[obj])
        
        remaining_items.sort(key=lambda x: x.order_index)
        
        for item in remaining_items:
            item.order_index = new_order
            new_order += 1
        
        # 重新编号，确保连续
        collection.renumber_order_indices()
        
        # 清理选择历史（可选）
        if _selection_history:
            _selection_history.clear()
        
        # 反馈信息
        if ordered_objects:
            if len(ordered_objects) == 1:
                self.report({'INFO'}, f"已将物体 '{ordered_objects[0].name}' 设为第一位")
            elif len(ordered_objects) <= 3:
                names_str = " → ".join([obj.name for obj in ordered_objects])
                self.report({'INFO'}, f"已按选择顺序设置: {names_str}")
            else:
                self.report({'INFO'}, f"已按选择顺序为 {len(ordered_objects)} 个物体设置新顺序")
        else:
            self.report({'WARNING'}, "没有可设置的物体")
        
        return {'FINISHED'}       

class BrushSelectModeOperator(bpy.types.Operator):
    """进入刷选模式，记录刷选顺序"""
    
    bl_idname = "object.brush_select_mode"
    bl_label = "刷选模式"
    bl_description = "进入刷选模式，按刷选顺序记录物体"
    bl_options = {'REGISTER'}
    
    _brush_selected_objects = []  # 存储刷选顺序
    
    def modal(self, context, event):
        """模态操作，持续监听"""
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # 退出刷选模式
            self.report({'INFO'}, f"刷选模式结束，记录了 {len(self._brush_selected_objects)} 个物体")
            return {'FINISHED'}
        
        # 监听选择变化
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # 获取当前活动物体（最新选择的）
            active_obj = context.active_object
            
            if active_obj and active_obj not in self._brush_selected_objects:
                self._brush_selected_objects.append(active_obj)
                self.report({'INFO'}, f"已记录: {active_obj.name} (第{len(self._brush_selected_objects)}个)")
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        """开始刷选模式"""
        self._brush_selected_objects = []
        
        # 进入模态操作
        context.window_manager.modal_handler_add(self)
        
        self.report({'INFO'}, "刷选模式已启动: 左键选择物体，右键/ESC退出")
        return {'RUNNING_MODAL'}

class RenumberCollectionOperator(bpy.types.Operator):
    """重新编号集合中的所有物体"""
    
    bl_idname = "object.renumber_collection"
    bl_label = "重新编号"
    bl_description = "将集合中物体的顺序编号重新从1开始排列"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if context.scene.active_collection_index < 0:
            self.report({'ERROR'}, "没有选中的集合")
            return {'CANCELLED'}
        
        collection = context.scene.collection_sets[context.scene.active_collection_index]
        
        if not collection.items:
            self.report({'WARNING'}, "集合中没有物体")
            return {'CANCELLED'}
        
        # 重新编号
        item_count = collection.renumber_order_indices()
        
        self.report({'INFO'}, f"已为集合 '{collection.name}' 中的 {item_count} 个物体重新编号")
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context.scene, 'collection_sets') and 
                len(context.scene.collection_sets) > 0 and
                context.scene.active_collection_index >= 0)

def register_operators():
    """注册操作符"""
    operators = [
        CollectObjectOperator,
        AddCollectionDirectOperator,
        RemoveCollectionOperator,
        RenameCollectionDirectOperator,
        RemoveCollectedObjectOperator,
        SelectCollectionByClickOperator,
        ViewAddSequenceOperator,
        BrushSelectModeOperator,
        RenumberCollectionOperator,
    ]
    
    for operator in operators:
        bpy.utils.register_class(operator)
    print("集合管理器操作符注册完成")

def unregister_operators():
    """注销操作符"""
    operators = [
        SelectCollectionByClickOperator,
        RemoveCollectedObjectOperator,
        RenameCollectionDirectOperator,
        RemoveCollectionOperator,
        AddCollectionDirectOperator,
        CollectObjectOperator,
        ViewAddSequenceOperator,
        BrushSelectModeOperator,
        RenumberCollectionOperator,
    ]
    
    for operator in operators:
        bpy.utils.unregister_class(operator)
    print("集合管理器操作符注销完成")