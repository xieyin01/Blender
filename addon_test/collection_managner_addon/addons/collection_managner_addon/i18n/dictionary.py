from collection_managner_addon.common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "zh_CN": {
        # 插件名称和主面板
        ("*", "Collection Manager"): "集合管理器",
        ("*", "Collection Manager Side Bar Panel"): "集合管理器面板",
        
        # 集合列表 (VIEW3D_UL_collection_sets 相关)
        ("*", "Collection List"): "集合列表",
        ("*", "Collection Name"): "集合名称",
        ("*", "Description"): "描述",
        ("*", "Color Tag"): "颜色标签",
        
        # 物体列表 (VIEW3D_UL_collection_items 相关)
        ("*", "Object List"): "物体列表",
        ("*", "Filter"): "过滤",
        ("*", "Order Index"): "顺序索引",
        
        # 操作符 (Operators) - 名称
        ("Operator", "收集物体"): "收集物体", # CollectObjectOperator.bl_label
        ("Operator", "添加集合"): "添加集合", # AddCollectionOperator.bl_label
        ("Operator", "删除集合"): "删除集合", # RemoveCollectionOperator.bl_label
        ("Operator", "重命名集合"): "重命名集合", # RenameCollectionOperator.bl_label
        ("Operator", "选择集合物体"): "选择集合物体", # SelectAllCollectedOperator.bl_label
        ("Operator", "从集合移除"): "从集合移除", # RemoveCollectedObjectOperator.bl_label
        
        # 操作符 (Operators) - 描述
        ("Operator", "Collect Objects"): "将选中的物体添加到当前集合",
        ("Operator", "Add Collection"): "添加一个新的集合",
        ("Operator", "Remove Collection"): "删除当前选中的集合",
        ("Operator", "Rename Collection"): "重命名当前集合",
        ("Operator", "Select Collection Objects"): "选择当前集合中的所有物体，支持过滤",
        ("Operator", "Remove from Collection"): "从当前集合中移除选中的物体",
        
        # 属性 (Properties)
        ("*", "Active Collection Index"): "当前集合索引",
        ("*", "Collection Items"): "集合物体",
        ("*", "Active Item Index"): "当前物体索引",
        ("*", "obj_description"): "物体描述",
        ("*", "Use Filter"): "使用过滤",
        
        # 界面按钮和标签文本
        ("*", "Add"): "添加",
        ("*", "Remove"): "移除",
        ("*", "Objects"): "个物体",
        ("*", "Please add a collection"): "请添加一个集合",
        ("*", "No collection selected"): "未选中集合",
        
        # 工具提示和说明（取自操作符的 bl_description）
        ("*", "Apply current filter to selection"): "在选择时应用当前过滤条件",
        ("*", "New collection name"): "新集合名称",
        
        # 进度/信息反馈（用户执行操作后显示的信息）
        ("*", "Added {0} objects to collection '{1}'"): "已添加 {0} 个物体到集合 '{1}'",
        ("*", "Collection '{0}' has been added"): "集合 '{0}' 已添加",
        ("*", "Collection '{0}' has been removed"): "集合 '{0}' 已删除",
        ("*", "Collection '{0}' has been renamed to '{1}'"): "集合 '{0}' 已重命名为 '{1}'",
        ("*", "Selected {0} objects"): "已选择 {0} 个物体",
        ("*", "Selected {0} objects (filter: '{1}')"): "已选择 {0} 个物体 (过滤: '{1}')",
        ("*", "Removed from collection '{0}'"): "已从集合 '{0}' 移除",
        ("*", "No objects in the collection"): "集合中没有物体",
        ("*", "No matching objects found"): "未找到匹配的物体",
        
        # 错误和警告信息
        ("*", "No collection selected"): "未选中集合",
        ("*", "No objects selected"): "未选中物体",
        ("*", "No selected collection item"): "未选中的集合项",
        ("*", "Collection name cannot be empty"): "集合名称不能为空",
        ("*", "Filter function import failed: {0}"): "过滤函数导入失败: {0}",
        ("*", "Filter error: {0}"): "过滤时出错: {0}",
        ("*", "{0} objects are not in the current view layer"): "{0} 个物体不在当前视图层",
        ("*", "{0} objects are hidden"): "{0} 个物体被隐藏",
        
        # 保留你原有的翻译项
        ("*", "Example Addon Side Bar Panel"): "示例插件面板",
        ("*", "Example Functions"): "示例功能",
        ("*", "ExampleAddon"): "示例插件",
        ("*", "Resource Folder"): "资源文件夹",
        ("*", "Int Config"): "整数参数",
        "Boolean Config": "布尔参数",
        "Second Panel": "第二面板",
        ("*", "Add-on Preferences View"): "插件设置面板",
        ("Operator", "ExampleOperator"): "示例操作",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]