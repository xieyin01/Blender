import re
from typing import List, Any, Optional, Tuple
from functools import lru_cache
import bpy


def filter_collected_items(
    items: List[Any],
    filter_name: str,
    search_fields: Optional[List[str]] = None,
    case_sensitive: bool = False,
    use_regex: bool = False,
    match_mode: str = 'smart',
    enable_cache: bool = True,
    batch_size: int = 1000
) -> Tuple[List[Any], List[int]]:
    """
    过滤项目列表，返回匹配的项目和它们在原列表中的索引。
    
    参数:
    - items: 要过滤的项目列表（可以是列表或bpy_prop_collection）
    - filter_name: 过滤文本
    - search_fields: 要搜索的字段列表，如果为None则尝试从项目中提取字符串
    - case_sensitive: 是否区分大小写
    - use_regex: 是否使用正则表达式
    - match_mode: 匹配模式 ('smart', 'contains', 'exact', 'startswith', 'endswith')
    - enable_cache: 是否启用缓存以提升性能
    - batch_size: 批量处理大小，用于内存优化
    
    返回:
    - Tuple[List[Any], List[int]]: (过滤后的项目列表, 在原列表中的索引列表)
    """
    
    # 如果过滤文本为空，返回所有项目
    if not filter_name:
        # 处理bpy_prop_collection类型（没有copy方法）
        if hasattr(items, 'values'):
            # 如果是bpy_prop_collection，转换为列表
            return list(items), list(range(len(items)))
        elif hasattr(items, '__iter__'):
            # 尝试复制可迭代对象
            try:
                # 先尝试list()
                return list(items), list(range(len(items)))
            except:
                # 如果不行，直接返回原列表
                return items, list(range(len(items)))
        else:
            # 最后的手段
            return items, list(range(len(items)))
    
    # 预处理过滤文本
    search_text = filter_name if case_sensitive else filter_name.lower()
    
    # 缓存函数：编译正则表达式
    @lru_cache(maxsize=32)
    def compile_regex(pattern: str, case_sensitive: bool) -> re.Pattern:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return re.compile(pattern, flags)
        except re.error:
            # 如果正则表达式无效，回退到普通字符串匹配
            return re.compile(re.escape(pattern), flags)
    
    # 从项目中提取搜索字符串的辅助函数（专门为Blender对象优化）
    def extract_search_string(item: Any) -> str:
        # 处理ObjectPointerProperty类型
        if hasattr(item, 'object_pointer') and item.object_pointer:
            obj = item.object_pointer
            # 尝试获取名称和描述
            name = getattr(obj, 'name', '')
            
            # 获取obj_description属性（从_addon_properties中定义）
            description = ""
            if hasattr(obj, 'obj_description'):
                description = getattr(obj, 'obj_description', '')
            
            return f"{name} {description}".strip()
        
        # 尝试识别Blender对象类型
        item_type = type(item).__name__
        
        # 处理Blender数据块
        if hasattr(item, 'type'):
            # 对象类型（Mesh, Camera, Light等）
            obj_type = getattr(item, 'type', '')
            if hasattr(item, 'name'):
                return f"{item.name} {obj_type}".strip()
        
        if search_fields is None:
            # 尝试从Blender对象中提取常见属性
            blender_attrs = ['name', 'id_name', 'type', 'data', 'location', 'dimensions']
            for attr in blender_attrs:
                if hasattr(item, attr):
                    value = getattr(item, attr, '')
                    # 对于嵌套对象（如data），尝试获取其名称
                    if attr == 'data' and hasattr(value, 'name'):
                        return str(value.name)
                    return str(value)
            
            # 如果是字典或简单对象
            if isinstance(item, dict):
                for field in ['name', 'id', 'title', 'label']:
                    if field in item:
                        return str(item[field])
                return str(item)
            else:
                return str(item)
        else:
            # 从指定字段中提取并组合字符串
            parts = []
            for field in search_fields:
                # 处理Blender对象属性访问
                if hasattr(item, field):
                    value = getattr(item, field, '')
                    # 特殊处理某些Blender属性
                    if field == 'data' and hasattr(value, 'name'):
                        value = value.name
                elif isinstance(item, dict) and field in item:
                    value = item.get(field, '')
                else:
                    value = ''
                parts.append(str(value))
            return ' '.join(parts)
    
    # 检查项目是否匹配的辅助函数
    def item_matches(item_text: str) -> bool:
        if not case_sensitive:
            item_text = item_text.lower()
        
        if use_regex:
            pattern = compile_regex(filter_name, case_sensitive)
            return bool(pattern.search(item_text))
        
        # 根据匹配模式进行判断
        if match_mode == 'smart':
            # 智能模式：根据过滤文本的格式自动选择匹配方式
            if '*' in search_text:
                # 通配符模式
                pattern = '^' + search_text.replace('*', '.*') + '$'
                try:
                    return bool(re.match(pattern, item_text))
                except:
                    return search_text in item_text
            elif ' ' in search_text:
                # 包含所有单词
                words = search_text.split()
                return all(word in item_text for word in words)
            else:
                # 默认：包含搜索文本
                return search_text in item_text
        elif match_mode == 'contains':
            return search_text in item_text
        elif match_mode == 'exact':
            return item_text == search_text
        elif match_mode == 'startswith':
            return item_text.startswith(search_text)
        elif match_mode == 'endswith':
            return item_text.endswith(search_text)
        else:
            # 默认使用包含模式
            return search_text in item_text
    
    # 批量处理函数（用于内存优化）
    def process_batch(batch_items: List[Any], start_idx: int) -> Tuple[List[Any], List[int]]:
        filtered_batch = []
        indices_batch = []
        
        for i, item in enumerate(batch_items):
            item_text = extract_search_string(item)
            if item_matches(item_text):
                filtered_batch.append(item)
                indices_batch.append(start_idx + i)
        
        return filtered_batch, indices_batch
    
    # 主过滤逻辑
    filtered_items = []
    filtered_indices = []
    
    # 获取项目总数（支持多种集合类型）
    try:
        items_count = len(items)
    except TypeError:
        # 如果无法获取长度，尝试转换为列表
        items = list(items)
        items_count = len(items)
    
    # 如果启用缓存且项目数量较大，使用缓存优化
    if enable_cache and items_count > 100:
        # 创建项目文本缓存
        item_text_cache = {}
        for idx, item in enumerate(items):
            item_text_cache[idx] = extract_search_string(item)
        
        # 使用缓存进行过滤
        for idx, item_text in item_text_cache.items():
            if item_matches(item_text):
                filtered_items.append(items[idx])
                filtered_indices.append(idx)
    else:
        # 批量处理
        if batch_size > 0 and items_count > batch_size:
            # 处理bpy_prop_collection的切片
            for batch_start in range(0, items_count, batch_size):
                batch_end = min(batch_start + batch_size, items_count)
                
                # 获取批次项目
                batch = []
                for i in range(batch_start, batch_end):
                    try:
                        batch.append(items[i])
                    except (IndexError, TypeError):
                        break
                
                batch_filtered, batch_indices = process_batch(batch, batch_start)
                filtered_items.extend(batch_filtered)
                filtered_indices.extend(batch_indices)
        else:
            # 一次性处理所有项目
            filtered_items, filtered_indices = process_batch(items, 0)
    
    return filtered_items, filtered_indices