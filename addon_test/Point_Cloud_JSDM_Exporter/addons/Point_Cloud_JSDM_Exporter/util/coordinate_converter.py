"""
坐标系转换工具
用于不同3D软件坐标系之间的转换
"""


class CoordinateSystemConverter:
    """坐标系转换器"""
    
    @staticmethod
    def convert(position, source_system='BLENDER', target_system='BLENDER', scale_factor=1.0):
        """
        转换坐标系
        
        Args:
            position: 原始位置 (x, y, z)
            source_system: 源坐标系 ('BLENDER', 'MAYA', 'UNITY', 'UNREAL')
            target_system: 目标坐标系 ('BLENDER', 'MAYA', 'UNITY', 'UNREAL')
            scale_factor: 缩放因子
        
        Returns:
            转换后的位置列表 [x, y, z]
        """
        # 确保位置是可迭代的
        if hasattr(position, '__iter__'):
            x, y, z = position[0], position[1], position[2]
        else:
            x, y, z = position.x, position.y, position.z
        
        # 如果源和目标相同，只应用缩放
        if source_system == target_system:
            return [
                x * scale_factor,
                y * scale_factor,
                z * scale_factor
            ]
        
        # 首先转换为Blender坐标系（作为中间坐标系）
        if source_system == 'BLENDER':
            blender_coords = [x, y, z]
        elif source_system == 'MAYA':
            # Maya: Y-up, 右手坐标系
            # Blender: Z-up, 右手坐标系
            # Maya到Blender: (x, y, z) -> (x, z, -y)
            blender_coords = [x, z, -y]
        elif source_system == 'UNITY':
            # Unity: Y-up, 左手坐标系
            # Blender: Z-up, 右手坐标系
            # Unity到Blender: (x, y, z) -> (x, z, y)
            blender_coords = [x, z, y]
        elif source_system == 'UNREAL':
            # Unreal: Z-up, 左手坐标系
            # Blender: Z-up, 右手坐标系
            # Unreal到Blender: (x, y, z) -> (x, -y, z)
            blender_coords = [x, -y, z]
        else:
            # 未知坐标系，保持原样
            blender_coords = [x, y, z]
        
        # 从Blender坐标系转换到目标坐标系
        if target_system == 'BLENDER':
            result = blender_coords
        elif target_system == 'MAYA':
            # Blender到Maya: (x, y, z) -> (x, -z, y)
            result = [blender_coords[0], -blender_coords[2], blender_coords[1]]
        else:
            # 未知坐标系，保持原样
            result = blender_coords
        
        # 应用缩放因子
        return [
            result[0] * scale_factor,
            result[1] * scale_factor,
            result[2] * scale_factor
        ]