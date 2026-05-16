from Point_Cloud_Exporter.common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "en_US": {
        "*": {
            # 插件名称和描述
            "Point Cloud JSDM Exporter": "Point Cloud JSDM Exporter",
            "导出几何节点JSDM格式数据": "Export geometry nodes JSDM format data",
            
            # 属性组名称
            "JSDM Export Settings": "JSDM Export Settings",
            
            # 导出设置
            "导出路径": "Export Path",
            "包含颜色": "Include Colors",
            "包含ID": "Include IDs",
            "导出动画": "Export Animation",
            "起始帧": "Start Frame",
            "结束帧": "End Frame",
            "帧步长": "Frame Step",
            "坐标系": "Coordinate System",
            "缩放因子": "Scale Factor",
            "调试模式": "Debug Mode",
            
            # 坐标系选项
            "Blender (Z-up)": "Blender (Z-up)",
            "Maya (Y-up)": "Maya (Y-up)",
            "Unity (Y-up)": "Unity (Y-up)",
            "Unreal Engine (Z-up)": "Unreal Engine (Z-up)",
            
            # 面板标题
            "几何节点JSDM导出器": "Geometry Nodes JSDM Exporter",
            "几何节点数据": "Geometry Nodes Data",
            
            # 操作符标签
            "导出JSDM": "Export JSDM",
            "检查几何节点数据": "Check Geometry Nodes Data",
            
            # 错误消息
            "未选择对象。请选择对象。": "No object selected. Please select an object.",
            "对象没有几何节点修改器。": "Object has no geometry nodes modifier.",
            "导出失败: {}": "Export failed: {}",
            "动画帧范围无效": "Invalid animation frame range",
            "导出动画中... 帧 {}": "Exporting animation... Frame {}",
            
            # 状态消息
            "请选择对象": "Please select an object",
            "对象:": "Object:",
            "几何节点:": "Geometry Nodes:",
            "数据统计": "Data Statistics",
            "点数量:": "Point Count:",
            "颜色数据:": "Color Data:",
            "ID数据:": "ID Data:",
            "动画信息:": "Animation Info:",
            "属性列表": "Attribute List",
            "数据操作": "Data Operations",
            "导出建议": "Export Recommendations",
            "动画帧范围": "Animation Frame Range",
            "动画帧率": "Animation Frame Rate"
        }
    },
    
    "zh_CN": {
        "*": {
            # 中文翻译
            "Point Cloud JSDM Exporter": "几何节点JSDM导出器",
            "导出几何节点JSDM格式数据": "导出几何节点JSDM格式数据",
            
            "JSDM Export Settings": "JSDM导出设置",
            
            "Export Path": "导出路径",
            "Include Colors": "包含颜色",
            "Include IDs": "包含ID",
            "Export Animation": "导出动画",
            "Start Frame": "起始帧",
            "End Frame": "结束帧",
            "Frame Step": "帧步长",
            "Coordinate System": "坐标系",
            "Scale Factor": "缩放因子",
            "Debug Mode": "调试模式",
            
            "Blender (Z-up)": "Blender (Z-up)",
            "Maya (Y-up)": "Maya (Y-up)",
            "Unity (Y-up)": "Unity (Y-up)",
            "Unreal Engine (Z-up)": "Unreal Engine (Z-up)",
            
            "Geometry Nodes JSDM Exporter": "几何节点JSDM导出器",
            "Geometry Nodes Data": "几何节点数据",
            
            "Export JSDM": "导出JSDM",
            "Check Geometry Nodes Data": "检查几何节点数据",
            
            "No object selected. Please select an object.": "未选择对象。请选择对象。",
            "Object has no geometry nodes modifier.": "对象没有几何节点修改器。",
            "Export failed: {}": "导出失败: {}",
            "Invalid animation frame range": "动画帧范围无效",
            "Exporting animation... Frame {}": "导出动画中... 帧 {}",
            
            "Please select an object": "请选择对象",
            "Object:": "对象:",
            "Geometry Nodes:": "几何节点:",
            "Data Statistics": "数据统计",
            "Point Count:": "点数量:",
            "Color Data:": "颜色数据:",
            "ID Data:": "ID数据:",
            "Animation Info:": "动画信息:",
            "Attribute List": "属性列表",
            "Data Operations": "数据操作",
            "Export Recommendations": "导出建议",
            "Animation Frame Range": "动画帧范围",
            "Animation Frame Rate": "动画帧率"
        }
    }
}

# 处理词典
dictionary = preprocess_dictionary(dictionary)

# 为简体中文添加别名
dictionary["zh_HANS"] = dictionary["zh_CN"]