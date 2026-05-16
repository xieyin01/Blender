import bpy
from bpy.props import StringProperty

class VIEW3D_UL_collection_sets(bpy.types.UIList):
    """集合列表UI（支持点击选择）"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        """绘制集合项"""
        try:
            if self.layout_type in {'DEFAULT', 'COMPACT'}:
                row = layout.row(align=True)
                
                # 集合颜色标签
                row.prop(item, "color_tag", text="", emboss=False, icon='COLOR')
                
                # 创建可点击的集合名称按钮
                op = row.operator(
                    "object.select_collection_by_click",
                    text=item.name, 
                    emboss=False, 
                    icon='GROUP'
                )
                op.collection_index = index
                
                # 物体数量
                row.label(text=f"({len(item.items)})")
                
            elif self.layout_type == 'GRID':
                layout.alignment = 'CENTER'
                layout.label(text="", icon_value=icon)
        except Exception as e:
            layout.label(text="Error", icon='ERROR')

class VIEW3D_UL_collection_items(bpy.types.UIList):
    """集合内物体列表UI"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        """绘制物体项"""
        try:
            if self.layout_type in {'DEFAULT', 'COMPACT'}:
                if item.object_pointer:
                    # 使用网格布局显示更多信息
                    grid = layout.grid_flow(row_major=True, columns=3, align=True)
                    
                    # 第一列：添加顺序编号
                    grid.label(text=f"{item.add_sequence:03d}.")
                    
                    # 第二列：物体名称和图标
                    row = grid.row(align=True)
                    row.label(text="", icon_value=icon)
                    row.prop(item.object_pointer, "name", text="", emboss=False)
                    
                    # 第三列：添加时间信息
                    if hasattr(item, 'added_frame') and item.added_frame > 0:
                        # 显示添加帧数
                        grid.label(text=f"帧:{item.added_frame}", icon='TIME')
                    else:
                        # 显示添加顺序
                        grid.label(text=f"#{item.order_index+1}")
                    
                    # 如果有描述，在下方显示
                    if hasattr(item.object_pointer, 'obj_description') and item.object_pointer.obj_description:
                        layout.label(text=item.object_pointer.obj_description, icon='TEXT')
            
            elif self.layout_type == 'GRID':
                layout.alignment = 'CENTER'
                # 在网格模式下显示简化的顺序信息
                if item.object_pointer:
                    layout.label(text=f"{item.add_sequence}", icon_value=icon)
        except Exception as e:
            layout.label(text="Error", icon='ERROR')
    
    # 过滤属性
    filter_name: bpy.props.StringProperty(
        name="Filter",
        default="",
        update=lambda self, context: self._on_filter_update(context),
        options={'TEXTEDIT_UPDATE'}
    )
    
    def _on_filter_update(self, context):
        """过滤更新时，保存到集合属性"""
        if hasattr(context.scene, 'collection_sets') and context.scene.active_collection_index >= 0:
            collection = context.scene.collection_sets[context.scene.active_collection_index]
            collection.filter_name = self.filter_name
    
    def filter_items(self, context, data, property):
        """过滤列表项"""
        try:
            items = getattr(data, property, [])
            
            # 获取当前过滤条件
            filter_text = ""
            if hasattr(self, 'filter_name') and self.filter_name:
                filter_text = self.filter_name
            elif (hasattr(context.scene, 'collection_sets') and 
                  context.scene.active_collection_index >= 0):
                collection = context.scene.collection_sets[context.scene.active_collection_index]
                filter_text = collection.filter_name
            
            # 如果不需要过滤，返回所有项
            if not filter_text:
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
                # 使用高级过滤函数（带缓存）
                filtered_items, filtered_indices = filter_collected_items(
                    items=items,
                    filter_name=filter_text,
                    search_fields=['name', 'obj_description'],
                    case_sensitive=False,
                    use_regex=False,
                    match_mode='smart',
                    enable_cache=True,
                    batch_size=100
                )
            else:
                # 备用过滤函数
                filter_lower = filter_text.lower()
                filtered_indices = []
                
                for idx, item in enumerate(items):
                    show = False
                    
                    # 使用缓存的搜索文本（性能优化）
                    if hasattr(item, 'cached_search_text') and item.cached_search_text:
                        if filter_lower in item.cached_search_text:
                            show = True
                    # 回退到原始检查
                    elif hasattr(item, 'object_pointer') and item.object_pointer:
                        obj = item.object_pointer
                        
                        # 检查对象名称
                        if hasattr(obj, 'name') and filter_lower in obj.name.lower():
                            show = True
                        
                        # 检查自定义描述字段
                        if not show and hasattr(item, 'obj_description'):
                            desc = getattr(item, 'obj_description', '')
                            if isinstance(desc, str) and filter_lower in desc.lower():
                                show = True
                    
                    if show:
                        filtered_indices.append(idx)
            
            # 创建过滤标志位列表
            filtered_flags = []
            for i in range(len(items)):
                if i in filtered_indices:
                    filtered_flags.append(self.bitflag_filter_item)
                else:
                    filtered_flags.append(0)
            
            # 保持原顺序
            ordered = list(range(len(items)))
            
            return filtered_flags, ordered
            
        except Exception as e:
            # 如果出现错误，返回所有项
            items = getattr(data, property, [])
            filtered_flags = [self.bitflag_filter_item] * len(items)
            ordered = list(range(len(items)))
            return filtered_flags, ordered

class CollectionManagerPanel(bpy.types.Panel):
    """集合管理器面板"""
    
    bl_label = "集合管理器"
    bl_idname = "SCENE_PT_collection_manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "集合管理器"
    
    def draw(self, context: bpy.types.Context):
        layout = self.layout
        
        # 集合列表部分
        box = layout.box()
        row = box.row()
        row.label(text="集合列表", icon='GROUP')
        
        # 直接添加集合的按钮，无确认对话框
        row.operator("object.add_collection_direct", icon="ADD", text="")
        
        if hasattr(context.scene, 'collection_sets') and context.scene.collection_sets:
            row = box.row()
            row.template_list(
                "VIEW3D_UL_collection_sets", 
                "", 
                context.scene, 
                "collection_sets", 
                context.scene, 
                "active_collection_index",
                rows=4
            )
            
            col = row.column(align=True)
            col.operator("object.remove_collection", icon="REMOVE", text="")
            col.operator("object.rename_collection_direct", icon="GREASEPENCIL", text="")
        
        # 当前集合内容部分
        if (hasattr(context.scene, 'collection_sets') and 
            len(context.scene.collection_sets) > 0 and
            context.scene.active_collection_index >= 0):
            
            collection = context.scene.collection_sets[context.scene.active_collection_index]
            
            # 集合信息标题
            layout.separator()
            row = layout.row(align=True)
            row.label(text=f"集合: {collection.name}", icon='GROUP')
            row.label(text=f"物体: {len(collection.items)}")
            
            # 集合描述（不使用box）
            if collection.description and collection.description.strip():
                layout.label(text=f"描述: {collection.description}", icon='TEXT')
            
            # 物体列表（不使用box，直接放在面板上）
            layout.separator()
            row = layout.row()
            row.template_list(
                "VIEW3D_UL_collection_items", 
                "", 
                collection, 
                "items", 
                collection, 
                "active_item_index",
                rows=6  # 限制显示行数
            )
            
            col = row.column(align=True)
            col.operator("object.collect_objects", icon="ADD", text="")
            col.operator("object.remove_collected_object", icon="REMOVE", text="")
            
            # 操作按钮
            layout.separator()
            row = layout.row()
            row.scale_y = 1.5
            
            row.operator("object.collect_objects")
            row.operator("object.set_custom_order")
            row.operator("object.view_add_sequence")
            row.operator("object.remove_collected_object")
            
            # 当前选中物体的描述编辑
            if collection.active_item_index >= 0 and collection.active_item_index < len(collection.items):
                item = collection.items[collection.active_item_index]
                if item.object_pointer:
                    layout.separator()
                    layout.prop(item.object_pointer, "obj_description", text="描述")
        else:
            layout.label(text="请添加一个集合", icon='INFO')

def register_panels():
    """注册面板和UI列表"""
    bpy.utils.register_class(VIEW3D_UL_collection_sets)
    bpy.utils.register_class(VIEW3D_UL_collection_items)
    bpy.utils.register_class(CollectionManagerPanel)
    print("集合管理器面板注册完成")

def unregister_panels():
    """注销面板和UI列表"""
    bpy.utils.unregister_class(CollectionManagerPanel)
    bpy.utils.unregister_class(VIEW3D_UL_collection_items)
    bpy.utils.unregister_class(VIEW3D_UL_collection_sets)
    print("集合管理器面板注销完成")