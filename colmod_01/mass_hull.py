"""
Mass Convex Hull Collision Generator.
Creates a single convex hull around all selected objects or face groups.
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
    duplicate_objects,
)


class MassHullModifierOperator(bpy.types.Operator):
    """Creates a single convex hull around all selected objects or face groups.
    
    All selected objects/faces are combined into one collision mesh.
    Original meshes are never modified - only new collision objects are created.
    """
    bl_idname = "colmod_01.create_mass_hull"
    bl_label = "Create Mass Hull"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create a single convex hull collision around all selected objects or faces"

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
            
            # Get the active object name for reference
            active_obj = get_active_mesh_object()
            reference_name = active_obj.name if active_obj else selected_objects[0].name
            
            # Track all created collision objects (before joining)
            created_objects = []
            
            if previous_mode == 'EDIT_MESH' and active_obj:
                # Process selected faces from Edit Mode
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(active_obj.data)
                
                for obj in selected_objects:
                    selected_verts = []
                    
                    if bm.faces:
                        for face in bm.faces:
                            if face.select:
                                for vert in face.verts:
                                    selected_verts.append(obj.matrix_world @ vert.co)
                    
                    if selected_verts:
                        # Create hull from selected faces
                        collision_obj = self._create_hull_from_vertices(
                            obj, selected_verts
                        )
                        created_objects.append(collision_obj)
                    else:
                        self.report({'WARNING'}, f"No faces selected in object: {obj.name}")
                
                bm.free()
            else:
                # Process entire objects
                created_objects = duplicate_objects(selected_objects)
            
            if not created_objects:
                self.report({'ERROR'}, "No collision objects were created.")
                return {'CANCELLED'}
            
            # Apply decimation to each object before joining
            for obj in created_objects:
                decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
                decimate_mod.ratio = decimate_ratio
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=decimate_mod.name)
            
            # Join all decimated objects into one
            select_only_objects(created_objects)
            bpy.ops.object.join()
            
            # Get the joined hull object
            hull_object = bpy.context.active_object
            
            # Apply convex hull to the joined object
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.convex_hull()
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Rename with Unreal Engine convention
            hull_object.name = get_unique_name(reference_name, "UCX_")
            
            # Assign collision material
            collision_material = get_collision_material()
            assign_material(hull_object, collision_material)
            
            # Deselect the collision object
            hull_object.select_set(False)
            
            # Restore original selection state
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_objects:
                if obj in bpy.data.objects:
                    obj.select_set(True)
            
            # Restore mode
            restore_mode(previous_mode)
            
            return {'FINISHED'}
            
        except Exception as e:
            # Restore mode on error
            restore_mode(previous_mode)
            self.report({'ERROR'}, f"Failed to create mass hull: {str(e)}")
            return {'CANCELLED'}

    def _create_hull_from_vertices(self, original_obj, vertices):
        """Create a mesh object from selected vertices with convex hull."""
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
        
        # Reset transform
        new_obj.location = (0, 0, 0)
        new_obj.rotation_euler = (0, 0, 0)
        new_obj.scale = (1, 1, 1)
        
        return new_obj


def register():
    bpy.utils.register_class(MassHullModifierOperator)


def unregister():
    bpy.utils.unregister_class(MassHullModifierOperator)


if __name__ == "__main__":
    register()
