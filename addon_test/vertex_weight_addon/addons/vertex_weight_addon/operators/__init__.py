import bpy


class SelectByWeightOperator(bpy.types.Operator):
    """Select vertices by weight threshold in the active vertex group"""
    bl_idname = "mesh.select_by_weight"
    bl_label = "Select by Weight"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ("ABOVE", "Above Threshold", "Select vertices with weight >= threshold"),
            ("BELOW", "Below Threshold", "Select vertices with weight <= threshold"),
            ("EQUALS", "Equals Zero", "Select vertices with weight == 0"),
            ("NONZERO", "Non-Zero", "Select vertices with weight > 0"),
        ],
        default="ABOVE",
    )  # type: ignore

    extend: bpy.props.BoolProperty(
        name="Extend Selection",
        description="Add to existing selection instead of replacing",
        default=False,
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return obj.vertex_groups.active is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mesh = obj.data
        threshold = context.scene.vw_weight_threshold
        group_index = obj.vertex_groups.active.index

        original_mode = obj.mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not self.extend:
            for vert in mesh.vertices:
                vert.select = False

        selected_count = 0
        for vert in mesh.vertices:
            weight = 0.0
            for g in vert.groups:
                if g.group == group_index:
                    weight = g.weight
                    break

            if self.mode == "ABOVE":
                select = weight >= threshold
            elif self.mode == "BELOW":
                select = weight <= threshold
            elif self.mode == "EQUALS":
                select = weight == 0.0
            elif self.mode == "NONZERO":
                select = weight > 0.0
            else:
                select = False

            if select:
                vert.select = True
                selected_count += 1

        mesh.update()

        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, f"Selected {selected_count} vertices")
        return {'FINISHED'}


class NormalizeWeightsOperator(bpy.types.Operator):
    """Normalize vertex weights so they sum to 1.0 (Spine2D style)"""
    bl_idname = "mesh.normalize_vertex_weights"
    bl_label = "Normalize Weights"
    bl_options = {'REGISTER', 'UNDO'}

    all_vertices: bpy.props.BoolProperty(
        name="All Vertices",
        description="Normalize all vertices instead of only selected",
        default=False,
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return len(obj.vertex_groups) > 0

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mesh = obj.data
        groups = obj.vertex_groups

        normalized_count = 0

        for vert in mesh.vertices:
            if not self.all_vertices and not vert.select:
                continue

            g_entries = list(vert.groups)
            if not g_entries:
                continue

            total = sum(g.weight for g in g_entries)
            if total > 0:
                for g_entry in g_entries:
                    groups[g_entry.group].add(
                        [vert.index], g_entry.weight / total, 'REPLACE'
                    )
                normalized_count += 1

        mesh.update()
        self.report({'INFO'}, f"Normalized weights for {normalized_count} vertices")
        return {'FINISHED'}


class CopyVertexWeightsOperator(bpy.types.Operator):
    """Copy weights from active vertex to selected vertices"""
    bl_idname = "mesh.copy_vertex_weights"
    bl_label = "Copy Vertex Weights"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        mode = context.active_object.mode
        if mode != 'EDIT':
            return False
        return True

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mesh = obj.data
        groups = obj.vertex_groups

        bpy.ops.object.mode_set(mode='OBJECT')

        active_vert = None
        selected_verts = []
        for vert in mesh.vertices:
            if vert.select:
                if active_vert is None:
                    active_vert = vert
                else:
                    selected_verts.append(vert)

        if active_vert is None:
            self.report({'ERROR'}, "No vertex selected")
            return {'CANCELLED'}

        if not selected_verts:
            self.report({'ERROR'}, "Need at least 2 selected vertices")
            return {'CANCELLED'}

        source_weights = list(active_vert.groups)
        copy_count = 0

        for target_vert in selected_verts:
            for g_entry in source_weights:
                groups[g_entry.group].add(
                    [target_vert.index], g_entry.weight, 'REPLACE'
                )
            copy_count += 1

        mesh.update()
        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, f"Copied weights to {copy_count} vertices")
        return {'FINISHED'}


class ToggleWeightOverlay(bpy.types.Operator):
    """Toggle vertex weight display overlay in 3D viewport"""
    bl_idname = "mesh.toggle_weight_overlay"
    bl_label = "Toggle Weight Display"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context: bpy.types.Context):
        context.scene.vw_display_weights = not context.scene.vw_display_weights

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report(
            {'INFO'},
            f"Weight display: {'ON' if context.scene.vw_display_weights else 'OFF'}"
        )
        return {'FINISHED'}
