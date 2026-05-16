import bpy


class VertexWeightEntry(bpy.types.PropertyGroup):
    """Single vertex weight entry"""
    vertex_index: bpy.props.IntProperty(name="Vertex Index")  # type: ignore
    group_name: bpy.props.StringProperty(name="Group Name")  # type: ignore
    weight: bpy.props.FloatProperty(
        name="Weight",
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )  # type: ignore
