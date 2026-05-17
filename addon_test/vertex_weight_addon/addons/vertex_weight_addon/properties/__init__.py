import bpy


class BoneWeightItem(bpy.types.PropertyGroup):
    """Single vertex weight entry for the active bone's weight list"""
    bl_label = "Bone Weight Item"
    bl_idname = "vw.bone_weight_item"
    vertex_index: bpy.props.IntProperty(name="Vertex")  # type: ignore
    weight: bpy.props.FloatProperty(
        name="Weight",
        min=0.0,
        max=1.0,
        default=0.0,
        subtype='FACTOR',
    )  # type: ignore
