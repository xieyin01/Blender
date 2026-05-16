import bpy

class ObjectPointerProperty(bpy.types.PropertyGroup):
    # object_pointer: bpy.props.PointerProperty(type=bpy.types.Object)    #type:ignore
    # 必须有 bl_label 和 bl_idname（可选）
    bl_label = "对象指针"
    bl_idname = "object_pointer_property"
    
    # 指向对象的指针
    object_pointer: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="对象",
        description="指向的Blender对象"
    )#type:ignore
    
    # 对象描述
    obj_description: bpy.props.StringProperty(
        name="描述",
        description="对象的自定义描述",
        default="",
        maxlen=256
    )#type:ignore
    
    # 收集时间（可选）
    collection_time: bpy.props.FloatProperty(
        name="收集时间",
        description="收集的时间戳",
        default=0.0
    )#type:ignore
    
    # 是否激活（可选）
    is_active: bpy.props.BoolProperty(
        name="激活",
        description="是否激活",
        default=False 
    )#type:ignore