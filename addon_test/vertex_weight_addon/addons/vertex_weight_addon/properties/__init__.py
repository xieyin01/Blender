import bpy


class BoneWeightItem(bpy.types.PropertyGroup):
    """Single vertex weight entry for the active bone's weight list"""
    vertex_index: bpy.props.IntProperty(name="Vertex")  # type: ignore
    weight: bpy.props.FloatProperty(
        name="Weight",
        min=0.0,
        max=1.0,
        default=0.0,
        subtype='FACTOR',
    )  # type: ignore
