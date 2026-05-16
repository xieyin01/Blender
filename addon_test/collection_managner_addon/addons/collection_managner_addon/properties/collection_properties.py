import bpy
from bpy.props import (
    CollectionProperty, 
    IntProperty, 
    StringProperty, 
    FloatVectorProperty, 
    PointerProperty,
    FloatProperty
)

class CollectionItem(bpy.types.PropertyGroup):
    """集合中的物体标签项"""
    
    # 物体指针
    object_pointer: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="关联的Blender物体"
    )
    
    # 物体在集合内的顺序
    order_index: bpy.props.IntProperty(
        name="Order Index",
        description="物体在集合中的顺序",
        default=0
    )
    
    # 添加时间戳
    added_timestamp: bpy.props.FloatProperty(
        name="Added Time",
        description="添加到集合的时间",
        default=0.0,
        precision=6
    )

    # 添加帧数（基于时间轴）
    added_frame: bpy.props.IntProperty(
        name="Added Frame",
        description="添加到集合时的帧数",
        default=0
    )
    
    # 添加顺序编号（基于添加顺序的唯一编号）
    add_sequence: bpy.props.IntProperty(
        name="Add Sequence",
        description="添加顺序编号（从1开始）",
        default=0
    )
    
    # 缓存搜索文本（性能优化）
    cached_search_text: bpy.props.StringProperty(
        name="Cached Search Text",
        description="缓存的搜索文本",
        default=""
    )

class CollectionSet(bpy.types.PropertyGroup):
    """集合定义"""
    
    # 集合名称
    name: bpy.props.StringProperty(
        name="Collection Name",
        description="集合名称",
        default="Collection",
        update=lambda self, context: self._on_name_update(context)
    )
    
    # 集合描述
    description: bpy.props.StringProperty(
        name="Description",
        description="集合描述",
        default=""
    )
    
    # 物体标签列表
    items: bpy.props.CollectionProperty(
        type=CollectionItem,
        name="Collection Items"
    )
    
    # 当前选中的物体索引
    active_item_index: bpy.props.IntProperty(
        name="Active Item Index",
        description="当前选中的物体索引",
        default=-1
    )
    
    # 集合颜色标签
    color_tag: bpy.props.FloatVectorProperty(
        name="Color Tag",
        description="集合颜色标签",
        subtype='COLOR',
        size=3,
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0
    )
    
    # 过滤属性
    filter_name: bpy.props.StringProperty(
        name="Filter",
        default="",
        options={'TEXTEDIT_UPDATE'}
    )

    # 添加一个计数器用于记录添加顺序
    next_sequence: bpy.props.IntProperty(
        name="Next Sequence",
        description="下一个添加顺序编号",
        default=1
    )
    
    def _on_name_update(self, context):
        """名称更新时的处理"""
        pass
    
    def get_sorted_items(self):
        """获取按顺序排序的物体列表"""
        return sorted(self.items, key=lambda x: x.order_index)
    
    def add_object(self, obj, context):
        """添加物体到集合（自动重新编号）"""
        
        # 检查是否已存在
        for item in self.items:
            if item.object_pointer == obj:
                return False
        
        # 创建新标签项
        new_item = self.items.add()
        new_item.object_pointer = obj
        
        # 记录添加顺序数据
        import time
        new_item.added_timestamp = context.scene.frame_current / context.scene.render.fps
        new_item.added_frame = context.scene.frame_current
        new_item.add_sequence = self.next_sequence
        self.next_sequence += 1
        
        # 将新物体添加到末尾
        if self.items:
            # 找到当前最大的order_index
            max_order = max((item.order_index for item in self.items), default=-1)
            new_item.order_index = max_order + 1
        else:
            new_item.order_index = 0
        
        # 缓存搜索文本
        if obj:
            name = obj.name if hasattr(obj, 'name') else ''
            desc = obj.obj_description if hasattr(obj, 'obj_description') else ''
            new_item.cached_search_text = f"{name} {desc}".lower().strip()
        
        # 自动重新编号，确保连续
        self.renumber_order_indices()
        
        return True

    def remove_object(self, obj):
        """从集合中移除物体（自动重新编号）"""
        removed = False
        
        for i, item in enumerate(self.items):
            if item.object_pointer == obj:
                # 从列表中移除
                self.items.remove(i)
                removed = True
                break
        
        if removed:
            # 重新编号
            self.renumber_order_indices()
        
        return removed
    
    def contains_object(self, obj):
        """检查集合是否包含指定物体"""
        for item in self.items:
            if item.object_pointer == obj:
                return True
        return False
    
    def move_item(self, from_index, to_index):
        """移动集合内物体的顺序"""
        if 0 <= from_index < len(self.items) and 0 <= to_index < len(self.items):
            item = self.items[from_index]
            self.items.remove(from_index)
            self.items.add()
            for i in range(len(self.items)-1, to_index, -1):
                self.items[i] = self.items[i-1]
            self.items[to_index] = item
            
            # 重新计算所有项的order_index
            for i, item in enumerate(self.items):
                item.order_index = i
            return True
        return False
    def renumber_order_indices(self):
        """重新编号order_index，使其从0开始连续"""
        # 按当前order_index排序
        sorted_items = sorted(self.items, key=lambda x: x.order_index)
        
        # 重新编号
        for i, item in enumerate(sorted_items):
            item.order_index = i
        
        return len(sorted_items)

# 插件属性定义
_addon_properties = {
    bpy.types.Object: {
        "obj_description": bpy.props.StringProperty(
            name="obj_description", 
            default="",
            description="物体描述"
        ),
    },
    bpy.types.Scene: {
        "collection_sets": bpy.props.CollectionProperty(
            type=CollectionSet,
            name="Collection Sets"
        ),
        "active_collection_index": bpy.props.IntProperty(
            name="Active Collection Index", 
            default=-1
        ),
        # 添加选择历史记录
        "selection_history": bpy.props.CollectionProperty(
            type=bpy.types.PropertyGroup,
            name="Selection History"
        ),
        "max_selection_history": bpy.props.IntProperty(
            name="Max History",
            default=100,
            min=10,
            max=1000
        ),
    }
}

def register_properties():
    """注册属性组"""
    bpy.utils.register_class(CollectionItem)
    bpy.utils.register_class(CollectionSet)
    
    # 添加插件属性
    for cls, props in _addon_properties.items():
        for prop_name, prop_value in props.items():
            if hasattr(cls, prop_name):
                try:
                    delattr(cls, prop_name)
                except AttributeError:
                    pass
            setattr(cls, prop_name, prop_value)
    print("集合管理器属性注册完成")

def unregister_properties():
    """注销属性组"""
    bpy.utils.unregister_class(CollectionSet)
    bpy.utils.unregister_class(CollectionItem)
    
    # 移除插件属性
    for cls, props in _addon_properties.items():
        for prop_name in props.keys():
            if hasattr(cls, prop_name):
                try:
                    delattr(cls, prop_name)
                except AttributeError:
                    pass
    print("集合管理器属性注销完成")