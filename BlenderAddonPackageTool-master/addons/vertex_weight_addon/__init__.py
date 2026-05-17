import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from .operators.AddonOperators import BoneWeightItem
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary

bl_info = {
    "name": "Vertex Weight Viewer",
    "author": "[Xieyin]",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": "Spine2D-style vertex weight display for faceless mesh models",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {
    bpy.types.Scene: {
        "vw_display_weights": bpy.props.BoolProperty(
            name="Display Weights",
            description="Show vertex weight labels in 3D viewport",
            default=False,
        ),
        "vw_text_size": bpy.props.IntProperty(
            name="Text Size",
            description="Font size for weight labels in viewport",
            default=14,
            min=8,
            max=48,
        ),
        "vw_color_mode": bpy.props.EnumProperty(
            name="Color Mode",
            description="Color scheme for weight display",
            items=[
                ("SPINE", "Spine2D", "Spine2D-style colors"),
                ("HEAT", "Heat", "Red (hot) to blue (cold)"),
                ("GRAY", "Grayscale", "Black to white"),
            ],
            default="SPINE",
        ),
        "vw_weight_threshold": bpy.props.FloatProperty(
            name="Weight Threshold",
            description="Minimum weight for vertex selection",
            default=0.01,
            min=0.0,
            max=1.0,
            subtype='FACTOR',
        ),
        "vw_bone_weights": bpy.props.CollectionProperty(
            type=BoneWeightItem,
            name="Bone Weights",
            description="Vertex weight entries for the active bone",
        ),
        "vw_active_weight_index": bpy.props.IntProperty(
            name="Active Weight Index",
            default=-1,
        ),
    },
}


def register():
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)
    print("{} addon is installed.".format(__addon_name__))


def unregister():
    bpy.app.translations.unregister(__addon_name__)
    auto_load.unregister()
    remove_properties(_addon_properties)
    print("{} addon is uninstalled.".format(__addon_name__))
