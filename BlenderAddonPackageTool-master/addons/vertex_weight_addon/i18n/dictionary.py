from common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "zh_CN": {
        ("*", "Vertex Weights"): "顶点权重",
        ("*", "Bones:"): "骨骼:",
        ("*", "Faceless mesh"): "无面网格",
        ("*", "Display Weights"): "显示权重",
        ("*", "Text Size"): "文字大小",
        ("*", "Color Mode"): "颜色模式",
        ("*", "Weight Threshold"): "权重阈值",
        ("*", "Select by Weight"): "按权重选择",
        ("*", "Normalize Weights"): "归一化权重",
        ("*", "Copy Weights"): "复制权重",
        ("*", "Toggle Weight Display"): "切换权重显示",
        ("*", "Show Overlay"): "显示叠加层",
        ("*", "Hide Overlay"): "隐藏叠加层",
        ("*", "Display Options"): "显示选项",
        ("*", "Vertex Weight Display Settings"): "顶点权重显示设置",
        ("*", "Max Weights Per Vertex"): "每顶点最大权重数",
        ("*", "Show Zero Weights"): "显示零权重",
        ("*", "Color Scheme"): "配色方案",
        ("*", "Apply to Mesh"): "应用到网格",
        ("*", "Select Verts"): "选择顶点",
        ("*", "Set All..."): "设置全部...",
        ("*", "Normalize"): "归一化",
        ("*", "Norm.All"): "归一化全部",
        "Select": "选择",
        "Weights": "权重",
        "verts": "顶点",
        "Vertices:": "顶点数:",
        "Object:": "物体:",
        ("Operator", "Select by Weight"): "按权重选择",
        ("Operator", "Normalize Weights"): "归一化权重",
        ("Operator", "Copy Vertex Weights"): "复制顶点权重",
        ("Operator", "Toggle Weight Display"): "切换权重显示",
        ("Operator", "Select Bone"): "选择骨骼",
        ("Operator", "Apply to Mesh"): "应用到网格",
        ("Operator", "Select Verts"): "选择顶点",
        ("Operator", "Set Weight Value"): "设置权重值",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]
