"""
几何节点数据读取工具
用于读取几何节点中的电子表格数据
"""

import bpy
from typing import Dict, List, Optional, Any


class GeometryNodesReader:
    """几何节点数据读取器"""
    
    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self.geometry_nodes_modifier = None
        self.node_tree = None
        
        # 查找几何节点修改器
        self._find_geometry_nodes_modifier()
    
    def _find_geometry_nodes_modifier(self) -> bool:
        """查找几何节点修改器"""
        if not self.obj:
            return False
        
        for mod in self.obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                self.geometry_nodes_modifier = mod
                self.node_tree = mod.node_group
                return True
        
        return False
    
    def has_geometry_nodes(self) -> bool:
        """检查对象是否有几何节点修改器"""
        return self.geometry_nodes_modifier is not None and self.node_tree is not None
    
    def get_spreadsheet_data(self) -> Dict[str, Any]:
        """
        获取电子表格数据
        
        Returns:
            包含位置、颜色等数据的字典
        """
        if not self.has_geometry_nodes():
            return {}
        
        try:
            # 获取评估后的数据
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = self.obj.evaluated_get(depsgraph)
            
            if not eval_obj:
                return {}
            
            # 获取几何数据
            if not hasattr(eval_obj.data, 'attributes'):
                return {}
            
            attributes = eval_obj.data.attributes
            spreadsheet_data = {
                'positions': [],
                'colors': [],
                'ids': [],
                'attributes': {}
            }
            
            # 查找位置属性（FLOAT_VECTOR类型）
            position_attr = None
            for attr_name, attr in attributes.items():
                if attr.data_type == 'FLOAT_VECTOR' and attr.domain == 'POINT':
                    position_attr = attr
                    break
            
            # 提取位置数据
            if position_attr:
                for item in position_attr.data:
                    if hasattr(item, 'vector'):
                        pos = item.vector
                    elif hasattr(item, 'value'):
                        pos = item.value
                    else:
                        pos = (0, 0, 0)
                    
                    spreadsheet_data['positions'].append([pos[0], pos[1], pos[2]])
            
            # 查找颜色属性
            color_attr = None
            for attr_name, attr in attributes.items():
                if attr.data_type in ['FLOAT_COLOR', 'BYTE_COLOR'] and attr.domain == 'POINT':
                    color_attr = attr
                    break
            
            # 提取颜色数据
            if color_attr:
                if color_attr.data_type == 'FLOAT_COLOR':
                    for item in color_attr.data:
                        if hasattr(item, 'color'):
                            color = item.color
                        else:
                            color = (1, 1, 1, 1)
                        
                        spreadsheet_data['colors'].append([
                            int(min(max(color[0], 0), 1) * 255),
                            int(min(max(color[1], 0), 1) * 255),
                            int(min(max(color[2], 0), 1) * 255)
                        ])
                else:  # BYTE_COLOR
                    for item in color_attr.data:
                        if hasattr(item, 'color'):
                            color = item.color
                        else:
                            color = (255, 255, 255, 255)
                        
                        spreadsheet_data['colors'].append([color[0], color[1], color[2]])
            
            # 查找ID属性
            id_attr = None
            for attr_name, attr in attributes.items():
                if attr.data_type == 'INT' and attr.domain == 'POINT':
                    id_attr = attr
                    break
            
            # 提取ID数据
            if id_attr:
                spreadsheet_data['ids'] = [item.value for item in id_attr.data]
            
            # 收集所有属性信息
            for attr_name, attr in attributes.items():
                spreadsheet_data['attributes'][attr_name] = {
                    'data_type': attr.data_type,
                    'domain': attr.domain,
                    'length': len(attr.data)
                }
            
            # 如果没有ID，生成连续ID
            if not spreadsheet_data['ids'] and spreadsheet_data['positions']:
                spreadsheet_data['ids'] = list(range(1, len(spreadsheet_data['positions']) + 1))
            
            # 如果没有颜色，填充默认颜色
            if not spreadsheet_data['colors'] and spreadsheet_data['positions']:
                spreadsheet_data['colors'] = [[255, 255, 255] for _ in range(len(spreadsheet_data['positions']))]
            
            return spreadsheet_data
            
        except Exception as e:
            print(f"获取几何节点数据失败: {str(e)}")
            return {}
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取几何节点元数据"""
        metadata = {
            'has_geometry_nodes': self.has_geometry_nodes(),
            'modifier_name': self.geometry_nodes_modifier.name if self.geometry_nodes_modifier else None,
            'node_tree_name': self.node_tree.name if self.node_tree else None,
            'attribute_count': 0,
            'attributes': []
        }
        
        if self.has_geometry_nodes():
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = self.obj.evaluated_get(depsgraph)
            
            if eval_obj and hasattr(eval_obj.data, 'attributes'):
                attributes = eval_obj.data.attributes
                metadata['attribute_count'] = len(attributes)
                
                for name, attr in attributes.items():
                    metadata['attributes'].append({
                        'name': name,
                        'data_type': attr.data_type,
                        'domain': attr.domain,
                        'length': len(attr.data)
                    })
        
        return metadata


def get_spreadsheet_summary(obj: bpy.types.Object) -> Dict[str, Any]:
    """获取电子表格数据摘要"""
    reader = GeometryNodesReader(obj)
    data = reader.get_spreadsheet_data()
    
    summary = {
        'has_geometry_nodes': reader.has_geometry_nodes(),
        'point_count': len(data.get('positions', [])),
        'has_colors': len(data.get('colors', [])) > 0,
        'has_ids': len(data.get('ids', [])) > 0,
        'attributes': list(data.get('attributes', {}).keys())
    }
    
    return summary