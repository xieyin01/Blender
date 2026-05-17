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
        return obj.mode == 'EDIT'

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

        state = 'ON' if context.scene.vw_display_weights else 'OFF'
        self.report({'INFO'}, f"Weight display: {state}")
        return {'FINISHED'}


def populate_weight_list(scene, obj, group_index):
    """Fill the CollectionProperty with vertices weighted to the given group"""
    items = scene.vw_bone_weights
    items.clear()
    mesh = obj.data

    for vert in mesh.vertices:
        for g in vert.groups:
            if g.group == group_index and g.weight > 0.0:
                item = items.add()
                item.vertex_index = vert.index
                item.weight = g.weight
                break

    scene.vw_active_weight_index = -1


class SelectBoneOperator(bpy.types.Operator):
    """Select a bone and show its weighted vertices"""
    bl_idname = "vw.select_bone"
    bl_label = "Select Bone"
    bl_options = {'REGISTER', 'UNDO'}

    group_index: bpy.props.IntProperty(default=-1)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return len(obj.vertex_groups) > 0

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if self.group_index < 0 or self.group_index >= len(obj.vertex_groups):
            self.report({'ERROR'}, "Invalid bone index")
            return {'CANCELLED'}

        obj.vertex_groups.active_index = self.group_index
        populate_weight_list(context.scene, obj, self.group_index)

        group_name = obj.vertex_groups[self.group_index].name
        self.report({'INFO'}, f"Showing weights for: {group_name}")
        return {'FINISHED'}


class ApplyWeightEditOperator(bpy.types.Operator):
    """Write edited weights back to the mesh vertex groups"""
    bl_idname = "vw.apply_weight_edit"
    bl_label = "Apply to Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return obj.vertex_groups.active is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        scene = context.scene
        group = obj.vertex_groups.active
        items = scene.vw_bone_weights

        if len(items) == 0:
            self.report({'WARNING'}, "No weights to apply")
            return {'CANCELLED'}

        applied = 0
        for item in items:
            new_weight = item.weight
            group.add([item.vertex_index], new_weight, 'REPLACE')
            applied += 1

        obj.data.update()

        # Refresh the list to reflect actual mesh state
        populate_weight_list(scene, obj, group.index)

        self.report({'INFO'}, f"Applied {applied} weight changes")
        return {'FINISHED'}


class SelectBoneVerticesOperator(bpy.types.Operator):
    """Select all vertices that have weight in the active bone"""
    bl_idname = "vw.select_bone_verts"
    bl_label = "Select Bone Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return obj.vertex_groups.active is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mesh = obj.data
        group = obj.vertex_groups.active

        original_mode = obj.mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        for vert in mesh.vertices:
            vert.select = False

        count = 0
        for vert in mesh.vertices:
            for g in vert.groups:
                if g.group == group.index and g.weight > 0.0:
                    vert.select = True
                    count += 1
                    break

        mesh.update()
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, f"Selected {count} vertices")
        return {'FINISHED'}


class SetWeightValueOperator(bpy.types.Operator):
    """Set weight to a specific value for all listed vertices"""
    bl_idname = "vw.set_weight_value"
    bl_label = "Set Weight Value"
    bl_options = {'REGISTER', 'UNDO'}

    target_weight: bpy.props.FloatProperty(
        name="Weight",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return False
        return len(context.scene.vw_bone_weights) > 0

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        items = scene.vw_bone_weights

        for item in items:
            item.weight = self.target_weight

        self.report({'INFO'}, f"Set {len(items)} vertices to weight: {self.target_weight:.3f}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
