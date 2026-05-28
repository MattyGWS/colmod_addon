"""
Individual Convex Hull Collision Generator.
Creates separate convex hulls for each selected object or face group.
"""
import bpy
import bmesh

from .utils import (
    get_selected_mesh_objects,
    get_active_mesh_object,
    ensure_object_mode,
    restore_mode,
    select_only_objects,
    get_unique_name,
    get_collision_material,
    assign_material,
    duplicate_object,
)


class IndividualHullModifierOperator(bpy.types.Operator):
    """Creates individual convex hulls around selected objects or groups of selected faces.
    
    Each selected object or face group gets its own convex hull collision mesh.
    Original meshes are never modified - only new collision objects are created.
    """
    bl_idname = "colmod_01.create_individual_hull"
    bl_label = "Create Individual Hull"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create separate convex hull collisions for each selected object or face group"

    def execute(self, context):
        # Store original selection and mode
        original_objects = set(bpy.context.selected_objects)
        previous_mode = ensure_object_mode()
        
        try:
            decimate_ratio = context.scene.colmod_decimate_ratio
            
            # Get selected mesh objects
            selected_objects = get_selected_mesh_objects()
            
            if not selected_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return {'CANCELLED'}
            
            # Track all created collision objects
            created_collision_objects = []
            
            for obj in selected_objects:
                # Check if we should process selected faces (from Edit Mode)
                if previous_mode == 'EDIT_MESH' and obj == get_active_mesh_object():
                    # Get selected faces/vertices
                    bpy.ops.object.mode_set(mode='EDIT')
                    bm = bmesh.from_edit_mesh(obj.data)
                    selected_verts = []
                    
                    if bm.faces:
                        for face in bm.faces:
                            if face.select:
                                for vert in face.verts:
                                    selected_verts.append(obj.matrix_world @ vert.co)
                    
                    bm.free()
                    
                    if selected_verts:
                        # Create hull from selected faces
                        collision_obj = self._create_hull_from_vertices(
                            obj, selected_verts, decimate_ratio
                        )
                        created_collision_objects.append(collision_obj)
                    else:
                        self.report({'WARNING'}, f"No faces selected in object: {obj.name}")
                else:
                    # Create hull from entire object
                    collision_obj = self._create_hull_from_object(obj, decimate_ratio)
                    created_collision_objects.append(collision_obj)
            
            if not created_collision_objects:
                self.report({'ERROR'}, "No collision objects were created.")
                return {'CANCELLED'}
            
            # Restore original selection state
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_objects:
                if obj.name in bpy.data.objects:
                    obj.select_set(True)
            
            # Restore mode
            restore_mode(previous_mode)
            
            return {'FINISHED'}
            
        except Exception as e:
            # Restore mode on error
            restore_mode(previous_mode)
            self.report({'ERROR'}, f"Failed to create individual hulls: {str(e)}")
            return {'CANCELLED'}

    def _create_hull_from_object(self, obj, decimate_ratio):
        """Create a convex hull collision from an entire object."""
        # Duplicate the object without modifying the original
        new_obj = duplicate_object(obj)
        
        # Apply convex hull
        self._apply_convex_hull_and_decimate(new_obj, decimate_ratio)
        
        return new_obj

    def _create_hull_from_vertices(self, original_obj, vertices, decimate_ratio):
        """Create a convex hull collision from selected vertices."""
        # Create a new mesh from the selected vertices
        mesh = bpy.data.meshes.new(f"{original_obj.name}_selected_faces")
        new_obj = bpy.data.objects.new(f"{original_obj.name}_selected_faces", mesh)
        bpy.context.collection.objects.link(new_obj)
        
        # Build mesh from vertices
        bm = bmesh.new()
        for vert in vertices:
            bm.verts.new(vert)
        bm.verts.ensure_lookup_table()
        bmesh.ops.convex_hull(bm, input=bm.verts)
        bm.to_mesh(mesh)
        bm.free()
        
        # Set transform to match original
        new_obj.location = original_obj.location
        new_obj.rotation_euler = original_obj.rotation_euler
        new_obj.scale = original_obj.scale
        
        # Apply decimation
        self._apply_convex_hull_and_decimate(new_obj, decimate_ratio)
        
        return new_obj

    def _apply_convex_hull_and_decimate(self, obj, decimate_ratio):
        """Apply convex hull and decimation to a collision object."""
        # Make this object active and selected
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # Apply convex hull in Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Apply decimation modifier
        decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate_mod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier=decimate_mod.name)
        
        # Rename with Unreal Engine convention
        base_name = obj.name.replace("_copy", "").replace("_selected_faces", "")
        obj.name = get_unique_name(base_name, "UCX_")
        
        # Assign collision material
        collision_material = get_collision_material()
        assign_material(obj, collision_material)
        
        # Deselect the collision object
        obj.select_set(False)


def register():
    bpy.utils.register_class(IndividualHullModifierOperator)


def unregister():
    bpy.utils.unregister_class(IndividualHullModifierOperator)


if __name__ == "__main__":
    register()
