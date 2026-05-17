import bpy
import blf

from ..config import __addon_name__
from ..operators.AddonOperators import (
    SelectByWeightOperator,
    NormalizeWeightsOperator,
    CopyVertexWeightsOperator,
    ToggleWeightOverlay,
)
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order

_draw_handles = {}


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


def draw_vertex_weight_overlay():
    """Draw weight labels on vertices in the 3D viewport"""
    context = bpy.context
    scene = context.scene

    if not scene.vw_display_weights:
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
        text_size = scene.vw_text_size
        color_scheme = scene.vw_color_mode
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
    """Spine2D-style vertex weight viewer panel"""
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

        # ---- Mesh info box ----
        box = layout.box()
        box.label(text=f"Mesh: {obj.name}  |  Verts: {len(mesh.vertices)}",
                   icon='MESH_DATA')
        if len(mesh.polygons) == 0:
            box.label(text="No face data (point cloud / faceless mesh)", icon='INFO')
        else:
            box.label(text=f"Faces: {len(mesh.polygons)}", icon='FACESEL')

        # ---- Vertex groups ----
        layout.separator()
        layout.label(text="Vertex Groups (Bones):", icon='GROUP_VERTEX')

        if len(obj.vertex_groups) == 0:
            layout.label(text="  No vertex groups found", icon='ERROR')
            return

        active_group = obj.vertex_groups.active
        if active_group:
            box = layout.box()
            box.prop_search(obj.vertex_groups, "active_index",
                            obj, "vertex_groups", text="Active")

            weight_count = 0
            total_weight = 0.0
            for vert in mesh.vertices:
                for g in vert.groups:
                    if g.group == active_group.index and g.weight > 0:
                        weight_count += 1
                        total_weight += g.weight

            box.label(text=f"  Vertices weighted: {weight_count}")
            if weight_count > 0:
                box.label(text=f"  Avg weight: {total_weight / weight_count:.3f}")

            col = box.column(align=True)
            col.prop(scene, "vw_weight_threshold", text="Threshold")
            op = col.operator(SelectByWeightOperator.bl_idname, text="Select Above")
            op.mode = "ABOVE"
            op = col.operator(SelectByWeightOperator.bl_idname, text="Select Non-Zero")
            op.mode = "NONZERO"

        # ---- Operators ----
        layout.separator()
        col = layout.column(align=True)
        col.operator(NormalizeWeightsOperator.bl_idname, text="Normalize Weights",
                      icon='NORMALIZE_WEIGHTS')
        col.operator(CopyVertexWeightsOperator.bl_idname, text="Copy Weights",
                      icon='COPYDOWN')

        # ---- Vertex detail ----
        layout.separator()
        layout.label(text="Vertex Weight Detail:", icon='VERTEXSEL')

        selected_count = sum(1 for v in mesh.vertices if v.select)
        if selected_count == 0:
            layout.label(text="  Select vertices to see weights")
            layout.label(text="  (Switch to Edit Mode, select vertices)")
            return

        layout.label(text=f"  {selected_count} vertices selected")

        if selected_count > 1:
            layout.label(text="  Select exactly one vertex for detail")
            return

        # Single vertex selected → show weight breakdown
        for vert in mesh.vertices:
            if not vert.select:
                continue

            box = layout.box()
            box.label(text=f"  Vertex #{vert.index}", icon='DOT')
            box.label(text=f"  Pos: ({vert.co.x:.2f}, {vert.co.y:.2f}, {vert.co.z:.2f})")

            if not vert.groups:
                box.label(text="  (no weights)", icon='BLANK1')
                break

            groups = [(g.group, g.weight) for g in vert.groups]
            groups.sort(key=lambda x: x[1], reverse=True)

            for group_idx, weight in groups:
                group_name = (obj.vertex_groups[group_idx].name
                              if group_idx < len(obj.vertex_groups)
                              else f"Group[{group_idx}]")
                row = box.row(align=True)
                row.label(text=f"    {group_name}")
                row.label(text=f"{weight:.4f}  ({weight * 100:.1f}%)")
            break


@reg_order(1)
class VIEW3D_PT_vertex_weight_list(BasePanel, bpy.types.Panel):
    bl_label = "Per-Group Weights"
    bl_idname = "VIEW3D_PT_vertex_weight_list"
    bl_parent_id = "VIEW3D_PT_vertex_weight_main"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        mesh = obj.data

        selected_count = sum(1 for v in mesh.vertices if v.select)
        if selected_count != 1 or len(obj.vertex_groups) == 0:
            layout.label(text="Select exactly one vertex")
            return

        for vert in mesh.vertices:
            if not vert.select:
                continue
            for g_entry in sorted(vert.groups, key=lambda x: x.weight, reverse=True):
                if g_entry.group >= len(obj.vertex_groups):
                    continue
                group = obj.vertex_groups[g_entry.group]
                row = layout.row(align=True)
                row.label(text=group.name)
                row.label(text=f"{g_entry.weight:.4f}")
            break


@reg_order(2)
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


def register_overlay_on_load():
    if bpy.context.scene.vw_display_weights:
        enable_overlay()


def register():
    enable_overlay()
    register_overlay_on_load()


def unregister():
    disable_overlay()
