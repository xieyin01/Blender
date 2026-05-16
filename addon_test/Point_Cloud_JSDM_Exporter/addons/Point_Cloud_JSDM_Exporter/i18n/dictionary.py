from Point_Cloud_JSDM_Exporter.common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "en_US": {
        "*": {
            # 插件名称和描述
            "Point Cloud JSDM Exporter": "Point Cloud JSDM Exporter",
            "导出JSDM格式的点云动画数据，包含动画和颜色导出功能": "Export point cloud animation data in JSDM format, including animation and color export functions",
            
            # 属性组名称
            "JSDM Export Settings": "JSDM Export Settings",
            "JSDM Animation Settings": "JSDM Animation Settings",
            
            # 导出设置
            "导出路径": "Export Path",
            "动画模式": "Animation Mode",
            "起始帧": "Start Frame",
            "结束帧": "End Frame",
            "帧步长": "Frame Step",
            "包含颜色": "Include Colors",
            "颜色模式": "Color Mode",
            "包含ID": "Include IDs",
            "坐标系": "Coordinate System",
            "缩放因子": "Scale Factor",
            "优化动画": "Optimize Animation",
            "移除重复帧": "Remove Duplicate Frames",
            "简化关键帧": "Simplify Keyframes",
            "简化阈值": "Simplify Threshold",
            "性能优化": "Use Performance Optimizer",
            "批处理大小": "Batch Size",
            "启用缓存": "Enable Cache",
            "调试模式": "Debug Mode",
            "详细日志": "Verbose Logging",
            
            # 动画设置
            "提取帧步长": "Extract Frame Step",
            "提取动画模式": "Extract Animation Mode",
            "提取包含颜色": "Extract Include Colors",
            "烘焙位置": "Bake Location",
            "烘焙旋转": "Bake Rotation",
            "烘焙缩放": "Bake Scale",
            "烘焙简化关键帧": "Bake Simplify Keyframes",
            "烘焙简化阈值": "Bake Simplify Threshold",
            "移除重复": "Remove Duplicates",
            "插值缺失": "Interpolate Missing",
            "最大间隔帧数": "Max Gap Frames",
            
            # 面板标题
            "点云JSDM导出器": "Point Cloud JSDM Exporter",
            "导出设置": "Export Settings",
            "动画设置": "Animation Settings",
            
            # 操作符标签
            "导出JSDM": "Export JSDM",
            "提取动画": "Extract Animation",
            "烘焙动画": "Bake Animation",
            "优化动画": "Optimize Animation",
            
            # 菜单项
            "JSDM (.jsdm)": "JSDM (.jsdm)",
            
            # 错误消息
            "未选择对象。请选择网格对象。": "No object selected. Please select a mesh object.",
            "对象类型无效。请选择网格对象。": "Invalid object type. Please select a mesh object.",
            "导出失败: {}": "Export failed: {}",
            "在选中的对象中未找到动画数据。": "No animation data found in the selected object.",
            
            # 状态消息
            "请选择网格对象": "Please select a mesh object",
            "对象:": "Object:",
            "顶点数:": "Vertices:",
            "动画:": "Animation:",
            "动画处理": "Animation Processing",
            "文件路径": "File Path",
            "文件设置": "File Settings",
            "动画设置": "Animation Settings",
            "数据设置": "Data Settings",
            "坐标系": "Coordinate System",
            "优化": "Optimization",
            "性能": "Performance",
            "调试": "Debug",
            "提取设置": "Extraction Settings",
            "烘焙设置": "Baking Settings",
            "优化设置": "Optimization Settings"
        },
        "Operator": {
            "导出JSDM格式点云动画数据": "Export point cloud animation data in JSDM format",
            "从选中对象提取动画数据": "Extract animation data from selected object",
            "烘焙动画到关键帧": "Bake animation to keyframes",
            "优化动画数据": "Optimize animation data"
        }
    },
    
    "zh_CN": {
        "*": {
            # 中文翻译
            "Point Cloud JSDM Exporter": "点云JSDM导出器",
            "导出JSDM格式的点云动画数据，包含动画和颜色导出功能": "导出JSDM格式的点云动画数据，包含动画和颜色导出功能",
            
            # 属性组名称
            "JSDM Export Settings": "JSDM导出设置",
            "JSDM Animation Settings": "JSDM动画设置",
            
            # 导出设置
            "Export Path": "导出路径",
            "Animation Mode": "动画模式",
            "Start Frame": "起始帧",
            "End Frame": "结束帧",
            "Frame Step": "帧步长",
            "Include Colors": "包含颜色",
            "Color Mode": "颜色模式",
            "Include IDs": "包含ID",
            "Coordinate System": "坐标系",
            "Scale Factor": "缩放因子",
            "Optimize Animation": "优化动画",
            "Remove Duplicate Frames": "移除重复帧",
            "Simplify Keyframes": "简化关键帧",
            "Simplify Threshold": "简化阈值",
            "Use Performance Optimizer": "使用性能优化",
            "Batch Size": "批处理大小",
            "Enable Cache": "启用缓存",
            "Debug Mode": "调试模式",
            "Verbose Logging": "详细日志",
            
            # 动画设置
            "Extract Frame Step": "提取帧步长",
            "Extract Animation Mode": "提取动画模式",
            "Extract Include Colors": "提取包含颜色",
            "Bake Location": "烘焙位置",
            "Bake Rotation": "烘焙旋转",
            "Bake Scale": "烘焙缩放",
            "Bake Simplify Keyframes": "烘焙简化关键帧",
            "Bake Simplify Threshold": "烘焙简化阈值",
            "Remove Duplicates": "移除重复",
            "Interpolate Missing": "插值缺失",
            "Max Gap Frames": "最大间隔帧数",
            
            # 面板标题
            "Point Cloud JSDM Exporter": "点云JSDM导出器",
            "Export Settings": "导出设置",
            "Animation Settings": "动画设置",
            
            # 操作符标签
            "Export JSDM": "导出JSDM",
            "Extract Animation": "提取动画",
            "Bake Animation": "烘焙动画",
            "Optimize Animation": "优化动画",
            
            # 菜单项
            "JSDM (.jsdm)": "JSDM (.jsdm)",
            
            # 错误消息（中文保持原样）
            "未选择对象。请选择网格对象。": "未选择对象。请选择网格对象。",
            "对象类型无效。请选择网格对象。": "对象类型无效。请选择网格对象。",
            "导出失败: {}": "导出失败: {}",
            "在选中的对象中未找到动画数据。": "在选中的对象中未找到动画数据。",
            
            # 状态消息
            "Please select a mesh object": "请选择网格对象",
            "Object:": "对象:",
            "Vertices:": "顶点数:",
            "Animation:": "动画:",
            "Animation Processing": "动画处理",
            "File Path": "文件路径",
            "File Settings": "文件设置",
            "Animation Settings": "动画设置",
            "Data Settings": "数据设置",
            "Coordinate System": "坐标系",
            "Optimization": "优化",
            "Performance": "性能",
            "Debug": "调试",
            "Extraction Settings": "提取设置",
            "Baking Settings": "烘焙设置",
            "Optimization Settings": "优化设置"
        }
    }
}

# 处理词典
dictionary = preprocess_dictionary(dictionary)

# 为简体中文添加别名
dictionary["zh_HANS"] = dictionary["zh_CN"]