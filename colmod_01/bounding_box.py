"""
Bounding Box Collision Generator.
Creates axis-aligned bounding boxes around selected objects or vertices.
"""
import bpy
import bmesh
from mathutils import Vector

from .utils import (
    get_selected_mesh_objects,
    get_active_mesh_object,
    ensure_object_mode,
    restore_mode,
    select_only_objects,
    get_unique_name,
    get_collision_material,
    assign_material,
)


class BoundingBoxModifierOperator(bpy.types.Operator):
    """Create a collision box around the selected object or vertices.
    
    Works in both Object Mode (selected objects) and Edit Mode (selected vertices).
    Original meshes are never modified - only new collision objects are created.
    """
    bl_idname = "colmod_01.create_bounding_box"
    bl_label = "Create Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create axis-aligned bounding box collision around selection"

    def execute(self, context):
        # Store original selection and mode
        original_objects = set(bpy.context.selected_objects)
        previous_mode = ensure_object_mode()
        
        try:
            # Get selected mesh objects
            selected_objects = get_selected_mesh_objects()
            
            if not selected_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return {'CANCELLED'}
            
            # Determine if we're working with vertex selection from Edit Mode
            was_edit_mode = (previous_mode == 'EDIT_MESH')
            active_obj = get_active_mesh_object()
            
            if was_edit_mode and active_obj:
                # We were in Edit Mode - get selected vertices
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(active_obj.data)
                selected_verts = [v.co for v in bm.verts if v.select]
                bm.free()
                
                if not selected_verts:
                    self.report({'ERROR'}, "No vertices selected in Edit Mode.")
                    return {'CANCELLED'}
                
                # Calculate bounds from selected vertices
                min_coords, max_coords = self._calculate_bounds_from_vertices(
                    selected_verts, active_obj
                )
                
                # Create the bounding box
                self._create_bounding_box(active_obj, min_coords, max_coords)
                
            else:
                # Object Mode - create bounds from all selected objects
                min_coords = Vector((float('inf'), float('inf'), float('inf')))
                max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
                
                for obj in selected_objects:
                    obj_min, obj_max = self._calculate_object_bounds(obj)
                    min_coords = Vector((
                        min(min_coords.x, obj_min.x),
                        min(min_coords.y, obj_min.y),
                        min(min_coords.z, obj_min.z),
                    ))
                    max_coords = Vector((
                        max(max_coords.x, obj_max.x),
                        max(max_coords.y, obj_max.y),
                        max(max_coords.z, obj_max.z),
                    ))
                
                # Use the first selected object as the reference for naming
                reference_obj = selected_objects[0]
                self._create_bounding_box(reference_obj, min_coords, max_coords)
            
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
            self.report({'ERROR'}, f"Failed to create bounding box: {str(e)}")
            return {'CANCELLED'}

    def _calculate_object_bounds(self, obj):
        """Calculate the min and max coordinates of an object's bounding box."""
        min_coords = Vector((float('inf'), float('inf'), float('inf')))
        max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for vertex in obj.data.vertices:
            global_coord = obj.matrix_world @ vertex.co
            min_coords.x = min(min_coords.x, global_coord.x)
            min_coords.y = min(min_coords.y, global_coord.y)
            min_coords.z = min(min_coords.z, global_coord.z)
            max_coords.x = max(max_coords.x, global_coord.x)
            max_coords.y = max(max_coords.y, global_coord.y)
            max_coords.z = max(max_coords.z, global_coord.z)
        
        return min_coords, max_coords

    def _calculate_bounds_from_vertices(self, vertices, obj):
        """Calculate the min and max coordinates from a list of vertices."""
        min_coords = Vector((float('inf'), float('inf'), float('inf')))
        max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for vertex in vertices:
            global_coord = obj.matrix_world @ vertex
            min_coords.x = min(min_coords.x, global_coord.x)
            min_coords.y = min(min_coords.y, global_coord.y)
            min_coords.z = min(min_coords.z, global_coord.z)
            max_coords.x = max(max_coords.x, global_coord.x)
            max_coords.y = max(max_coords.y, global_coord.y)
            max_coords.z = max(max_coords.z, global_coord.z)
        
        return min_coords, max_coords

    def _create_bounding_box(self, original_obj, min_coords, max_coords):
        """Create a bounding box mesh at the specified coordinates."""
        # Calculate dimensions and center
        dimensions = max_coords - min_coords
        location = (min_coords + max_coords) * 0.5
        
        # Create cube at the calculated location
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        bounding_box_obj = bpy.context.active_object
        bounding_box_obj.scale = dimensions
        
        # Set the bounding box's name with Unreal Engine convention
        base_name = original_obj.name
        bounding_box_obj.name = get_unique_name(base_name, "UBX_")
        
        # Assign collision material
        collision_material = get_collision_material()
        assign_material(bounding_box_obj, collision_material)
        
        # Deselect the new collision object
        bounding_box_obj.select_set(False)


def register():
    bpy.utils.register_class(BoundingBoxModifierOperator)


def unregister():
    bpy.utils.unregister_class(BoundingBoxModifierOperator)


if __name__ == "__main__":
    register()
