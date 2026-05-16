import bpy
from .properties import register_properties, unregister_properties
from .operators import register_operators, unregister_operators
from .panels import register_panels, unregister_panels


from bpy.app.handlers import persistent
# 全局变量，用于存储上一个选择状态
_last_selection_state = None

@persistent
def auto_update_collection_order(scene):
    """自动检测选择变化并更新集合顺序"""
    global _last_selection_state
    
    try:
        # 检查当前是否有活动的集合
        if not hasattr(scene, 'collection_sets') or scene.active_collection_index < 0:
            _last_selection_state = None
            return
        
        collection = scene.collection_sets[scene.active_collection_index]
        
        # 获取当前选中的物体
        current_selection = tuple(sorted(obj.name for obj in bpy.context.selected_objects))
        
        # 如果选择状态没有变化，直接返回
        if current_selection == _last_selection_state:
            return
        
        _last_selection_state = current_selection
        
        # 筛选出在当前集合中的选中物体
        collection_objects = [item.object_pointer for item in collection.items if item.object_pointer]
        valid_objects = [obj for obj in bpy.context.selected_objects if obj in collection_objects]
        
        # 只有当选择2个或更多物体时才自动重新排序
        if len(valid_objects) >= 2:
            # 创建物体到集合项的映射
            item_dict = {}
            for item in collection.items:
                if item.object_pointer:
                    item_dict[item.object_pointer] = item
            
            # 按照选择顺序设置新的order_index
            new_order = 0
            
            # 处理用户选中的物体（按选择顺序）
            for obj in valid_objects:
                if obj in item_dict:
                    item = item_dict[obj]
                    item.order_index = new_order
                    new_order += 1
            
            # 处理剩下的物体（保持原来的相对顺序）
            remaining_objects = [obj for obj in collection_objects if obj not in valid_objects]
            
            remaining_items = []
            for obj in remaining_objects:
                if obj in item_dict:
                    remaining_items.append(item_dict[obj])
            
            remaining_items.sort(key=lambda x: x.order_index)
            
            for item in remaining_items:
                item.order_index = new_order
                new_order += 1
            
            # 可选：打印调试信息
            if bpy.context.preferences.view.show_developer_ui:
                print(f"自动更新集合 '{collection.name}' 顺序: {[obj.name for obj in valid_objects]}")
                
    except Exception as e:
        # 避免因错误导致整个事件系统崩溃
        if bpy.context.preferences.view.show_developer_ui:
            print(f"自动更新集合顺序时出错: {e}")

# 存储上一次的选择状态
_last_selection = set()

@persistent
def track_selection_history(scene, depsgraph=None):
    """跟踪选择历史，记录选择顺序"""
    global _last_selection
    
    try:
        # 获取当前选中的物体
        current_selection = set(context.selected_objects)
        
        # 如果选择没有变化，直接返回
        if current_selection == _last_selection:
            return
        
        # 找出新增的物体（刚刚被选中的）
        new_selections = current_selection - _last_selection
        
        # 更新选择历史
        if new_selections:
            for obj in new_selections:
                # 添加到历史记录
                if hasattr(scene, 'selection_history'):
                    # 检查是否已存在
                    existing = False
                    for item in scene.selection_history:
                        if item.object_pointer == obj:
                            existing = True
                            break
                    
                    if not existing:
                        new_item = scene.selection_history.add()
                        new_item.object_pointer = obj
                        new_item.timestamp = scene.frame_current
                        
                        # 限制历史记录大小
                        if len(scene.selection_history) > scene.max_selection_history:
                            scene.selection_history.remove(0)
        
        _last_selection = current_selection
        
    except Exception as e:
        # 静默处理错误，避免影响正常使用
        pass

_selection_history = []

@persistent
def capture_selection_history(scene):
    """捕获选择历史，记录选择的顺序"""
    global _selection_history
    
    # 获取当前选中的物体
    selected_objects = bpy.context.selected_objects
    
    if not selected_objects:
        return
    
    # 找出新增的选择（与上一次比较）
    current_selection = set(selected_objects)
    
    # 如果选择历史为空，直接添加所有选中的物体
    if not _selection_history:
        _selection_history.extend(selected_objects)
        return
    
    # 检查每个选中的物体是否已经在历史中
    for obj in selected_objects:
        if obj not in _selection_history:
            # 新选择的物体，添加到历史末尾
            _selection_history.append(obj)

# Add-on info
bl_info = {
    "name": "集合管理器",
    "author": "Xieyin",
    "blender": (3, 5, 0),
    "version": (1, 0, 0),
    "description": "高效的集合标签管理系统",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View"
}

def register():
    """注册插件所有组件"""
    print("注册集合管理器插件...")
    register_properties()
    register_operators()
    register_panels()

    # 注册选择历史处理器
    if capture_selection_history not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(capture_selection_history)

    print("集合管理器插件注册完成")

def unregister():
    """注销插件所有组件"""
    print("注销集合管理器插件...")

    # 注销选择历史处理器
    if capture_selection_history in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(capture_selection_history)
    
    unregister_panels()
    unregister_operators()
    unregister_properties()
    print("集合管理器插件注销完成")

    # 清理全局变量
    global _selection_history, _last_selection_count
    _selection_history.clear()
    _last_selection_count = 0

if __name__ == "__main__":
    register()