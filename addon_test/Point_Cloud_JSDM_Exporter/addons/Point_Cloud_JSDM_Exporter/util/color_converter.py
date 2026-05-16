"""
颜色转换工具
用于不同颜色格式之间的转换
"""


class ColorConverter:
    """颜色转换器"""
    
    @staticmethod
    def float_to_byte(color):
        """
        浮点颜色 (0.0-1.0) 转换为字节颜色 (0-255)
        
        Args:
            color: 浮点颜色列表 [r, g, b] 或 [r, g, b, a]
        
        Returns:
            字节颜色列表 [r, g, b]
        """
        if color is None:
            return None
        
        # 确保颜色是列表
        if not isinstance(color, (list, tuple)):
            return None
        
        # 处理RGBA颜色，只取RGB
        if len(color) >= 3:
            return [
                int(min(max(color[0], 0.0), 1.0) * 255),
                int(min(max(color[1], 0.0), 1.0) * 255),
                int(min(max(color[2], 0.0), 1.0) * 255)
            ]
        
        return None
    
    @staticmethod
    def byte_to_float(color):
        """
        字节颜色 (0-255) 转换为浮点颜色 (0.0-1.0)
        
        Args:
            color: 字节颜色列表 [r, g, b] 或 [r, g, b, a]
        
        Returns:
            浮点颜色列表 [r, g, b, 1.0]
        """
        if color is None:
            return None
        
        # 确保颜色是列表
        if not isinstance(color, (list, tuple)):
            return None
        
        # 处理RGB或RGBA颜色
        if len(color) >= 3:
            return [
                color[0] / 255.0,
                color[1] / 255.0,
                color[2] / 255.0,
                1.0  # 默认alpha值
            ]
        
        return None