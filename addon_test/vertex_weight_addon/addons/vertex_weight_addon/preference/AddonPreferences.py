import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty
from bpy.types import AddonPreferences

from ..config import __addon_name__


class VertexWeightPreferences(AddonPreferences):
    bl_idname = __addon_name__

    overlay_text_size: IntProperty(
        name="Overlay Text Size",
        description="Font size for weight overlay in viewport",
        default=14,
        min=8,
        max=48,
    )

    overlay_opacity: FloatProperty(
        name="Overlay Opacity",
        default=1.0,
        min=0.1,
        max=1.0,
        subtype='FACTOR',
    )

    max_weights_per_vertex: IntProperty(
        name="Max Weights Per Vertex",
        description="Maximum number of bone weights shown per vertex (Spine2D: 4)",
        default=4,
        min=1,
        max=8,
    )

    show_zero_weights: BoolProperty(
        name="Show Zero Weights",
        description="Also display vertex groups with zero weight",
        default=False,
    )

    color_scheme: EnumProperty(
        name="Color Scheme",
        items=[
            ("SPINE2D", "Spine2D", "Spine2D-style blue-red gradient"),
            ("HEAT", "Heat Map", "Classic heat map colors"),
            ("GRAY", "Grayscale", "Black to white gradient"),
        ],
        default="SPINE2D",
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text="Vertex Weight Display Settings")
        layout.prop(self, "overlay_text_size")
        layout.prop(self, "overlay_opacity")
        layout.prop(self, "max_weights_per_vertex")
        layout.prop(self, "show_zero_weights")
        layout.prop(self, "color_scheme")
