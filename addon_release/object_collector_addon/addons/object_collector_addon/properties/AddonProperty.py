import bpy

class ObjectPointerProperty(bpy.types.PropertyGroup):
    object_pointer: bpy.props.PointerProperty(type=bpy.types.Object)    #type:ignore