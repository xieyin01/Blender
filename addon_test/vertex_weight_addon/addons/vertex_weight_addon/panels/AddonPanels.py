import bpy
import blf

from ..config import __addon_name__
from ..operators.AddonOperators import (
    SelectByWeightOperator,
    NormalizeWeightsOperator,
    CopyVertexWeightsOperator,
    ToggleWeightOverlay,
    SelectBoneOperator,
    ApplyWeightEditOperator,
    SelectBoneVerticesOperator,
    SetWeightValueOperator,
)
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order

_draw_handles = {}


# ═══════════════════════════════════════════════════════════════
#  Color helpers
# ═══════════════════════════════════════════════════════════════

def get_weight_color(weight, scheme="SPINE2D"):
    """Get RGBA color for a weight value (0.0 ~ 1.0)"""
    w = max(0.0, min(1.0, weight))
    if scheme == "SPINE2D":
        r = 0.2 + w * 0.8
        g = 0.3 + w * 0.5
        b = 1.0 - w * 0.7
        return (r, g, b, 1.0)
    elif scheme == "HEAT":
        if w < 0.25:
            return (0.0, w * 4.0, 1.0, 1.0)
        elif w < 0.5:
            return (0.0, 1.0, 1.0 - (w - 0.25) * 4.0, 1.0)
        elif w < 0.75:
            return ((w - 0.5) * 4.0, 1.0, 0.0, 1.0)
        else:
            return (1.0, 1.0 - (w - 0.75) * 4.0, 0.0, 1.0)
    else:
        return (w, w, w, 1.0)


# ═══════════════════════════════════════════════════════════════
#  Viewport overlay
# ═══════════════════════════════════════════════════════════════

def draw_vertex_weight_overlay():
    """Draw weight labels on vertices in the 3D viewport"""
    context = bpy.context
    scene = context.scene

    if not getattr(scene, "vw_display_weights", False):
        return

    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return

    mesh = obj.data
    prefs = context.preferences.addons.get(__addon_name__)
    if prefs:
        prefs = prefs.preferences
        text_size = prefs.overlay_text_size
        color_scheme = prefs.color_scheme
        max_weights = prefs.max_weights_per_vertex
        show_zero = prefs.show_zero_weights
    else:
        text_size = getattr(scene, "vw_text_size", 14)
        color_scheme = getattr(scene, "vw_color_mode", "SPINE")
        max_weights = 4
        show_zero = False

    font_id = 0
    blf.size(font_id, text_size)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font_id, 1, -1)

    try:
        from bpy_extras import view3d_utils
    except ImportError:
        return

    active_group = obj.vertex_groups.active
    active_group_index = active_group.index if active_group else -1
    matrix_world = obj.matrix_world
    region = context.region
    rv3d = context.space_data.region_3d

    for vert in mesh.vertices:
        groups_on_vert = []
        for g in vert.groups:
            if g.weight > 0.0 or show_zero:
                groups_on_vert.append((g.group, g.weight))

        if not groups_on_vert:
            continue

        if active_group_index >= 0:
            groups_on_vert = [g for g in groups_on_vert if g[0] == active_group_index]

        groups_on_vert.sort(key=lambda x: x[1], reverse=True)
        groups_on_vert = groups_on_vert[:max_weights]

        world_co = matrix_world @ vert.co
        co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, world_co)

        if co_2d is None:
            continue

        x, y = int(co_2d.x), int(co_2d.y)

        for i, (group_idx, weight) in enumerate(groups_on_vert):
            color = get_weight_color(weight, color_scheme)
            blf.color(font_id, color[0], color[1], color[2], color[3])
            group_name = obj.vertex_groups[group_idx].name if group_idx < len(obj.vertex_groups) else "?"
            label = f"{group_name}: {weight:.2f}"
            blf.position(font_id, x + 8, y - i * (text_size + 2), 0)
            blf.draw(font_id, label)


def enable_overlay():
    global _draw_handles
    if "weight_overlay" not in _draw_handles:
        _draw_handles["weight_overlay"] = bpy.types.SpaceView3D.draw_handler_add(
            draw_vertex_weight_overlay, (), 'WINDOW', 'POST_PIXEL'
        )


def disable_overlay():
    global _draw_handles
    if "weight_overlay" in _draw_handles:
        bpy.types.SpaceView3D.draw_handler_remove(
            _draw_handles["weight_overlay"], 'WINDOW'
        )
        del _draw_handles["weight_overlay"]


# ═══════════════════════════════════════════════════════════════
#  UILists
# ═══════════════════════════════════════════════════════════════

class VIEW3D_UL_weight_list(bpy.types.UIList):
    """Display vertex index and weight for the active bone"""
    bl_idname = "VIEW3D_UL_weight_list"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index=0, flt_flag=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=f"#{item.vertex_index}", icon='DOT')
            row.prop(item, "weight", text="", emboss=True, slider=True)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=f"#{item.vertex_index}: {item.weight:.2f}")


# ═══════════════════════════════════════════════════════════════
#  Panels
# ═══════════════════════════════════════════════════════════════

class BasePanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VertexWeight"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'


@reg_order(0)
class VIEW3D_PT_vertex_weight_main(BasePanel, bpy.types.Panel):
    """Spine2D-style bone weight editor"""
    bl_label = "Vertex Weights"
    bl_idname = "VIEW3D_PT_vertex_weight_main"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene
        mesh = obj.data

        # ---- Toggle overlay ----
        row = layout.row(align=True)
        icon = 'HIDE_OFF' if scene.vw_display_weights else 'HIDE_ON'
        label = "Hide Overlay" if scene.vw_display_weights else "Show Overlay"
        row.operator(ToggleWeightOverlay.bl_idname, text=label, icon=icon,
                      depress=scene.vw_display_weights)

        # ---- Mesh info ----
        box = layout.box()
        box.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')
        row = box.row(align=True)
        row.label(text=f"Vertices: {len(mesh.vertices)}")
        if len(mesh.polygons) == 0:
            row.label(text="|  Faceless mesh", icon='INFO')
        else:
            row.label(text=f"|  Faces: {len(mesh.polygons)}")

        # ---- Bone list ----
        layout.separator()
        layout.label(text="Bones:", icon='BONE_DATA')

        if len(obj.vertex_groups) == 0:
            layout.label(text="  No bones (vertex groups)", icon='ERROR')
            return

        box = layout.box()
        active_idx = obj.vertex_groups.active_index
        for idx, group in enumerate(obj.vertex_groups):
            # Count weighted vertices for this group
            vcount = 0
            for vert in mesh.vertices:
                for g in vert.groups:
                    if g.group == idx and g.weight > 0.0:
                        vcount += 1
                        break

            row = box.row(align=True)
            # Highlight active bone
            if idx == active_idx:
                row.label(text=f"▸ {group.name}", icon='GROUP_VERTEX')
            else:
                row.label(text=f"  {group.name}", icon='BLANK1')

            row.label(text=f"{vcount} verts")

            op = row.operator(SelectBoneOperator.bl_idname, text="Select")
            op.group_index = idx

        # ---- Weight editor box ----
        if obj.vertex_groups.active is None:
            return

        layout.separator()
        active_group = obj.vertex_groups.active
        box = layout.box()
        box.label(
            text=f"{active_group.name} — Weights",
            icon='GROUP_VERTEX'
        )

        items = scene.vw_bone_weights

        if len(items) == 0:
            box.label(text="  Click [Select] on a bone to load weights")
            return

        # Weight list
        box.template_list(
            "VIEW3D_UL_weight_list", "",
            scene, "vw_bone_weights",
            scene, "vw_active_weight_index",
            rows=min(6, len(items)),
        )

        # Edit selected weight
        idx = scene.vw_active_weight_index
        if 0 <= idx < len(items):
            item = items[idx]
            row = box.row(align=True)
            row.label(text=f"  Vertex #{item.vertex_index}", icon='DOT')
            col = row.column()
            col.prop(item, "weight", text="", slider=True)
            row.label(text=f"{item.weight * 100:.1f}%")

        # Action buttons
        row = box.row(align=True)
        row.operator(ApplyWeightEditOperator.bl_idname,
                      text="Apply to Mesh", icon='CHECKMARK')
        row.operator(SelectBoneVerticesOperator.bl_idname,
                      text="Select Verts", icon='RESTRICT_SELECT_OFF')

        row = box.row(align=True)
        op = row.operator(SetWeightValueOperator.bl_idname,
                           text="Set All...", icon='PROPERTIES')
        row.operator(NormalizeWeightsOperator.bl_idname,
                      text="Normalize", icon='NORMALIZE_WEIGHTS')
        op_all = row.operator(NormalizeWeightsOperator.bl_idname,
                               text="Norm.All")
        op_all.all_vertices = True


@reg_order(1)
class VIEW3D_PT_vertex_weight_display_opts(BasePanel, bpy.types.Panel):
    bl_label = "Display Options"
    bl_idname = "VIEW3D_PT_vertex_weight_display_opts"
    bl_parent_id = "VIEW3D_PT_vertex_weight_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "vw_text_size")
        layout.prop(scene, "vw_color_mode")
        layout.prop(scene, "vw_weight_threshold")


# ═══════════════════════════════════════════════════════════════
#  Registration helpers
# ═══════════════════════════════════════════════════════════════

def register_overlay_on_load():
    try:
        if getattr(bpy.context.scene, "vw_display_weights", False):
            enable_overlay()
    except AttributeError:
        pass


def register():
    enable_overlay()
    register_overlay_on_load()


def unregister():
    disable_overlay()
