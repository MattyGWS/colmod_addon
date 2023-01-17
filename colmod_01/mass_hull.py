import bpy
from mathutils import Vector

class MassHullModifierOperator(bpy.types.Operator):
    """Applies a decimate modifier set to collapse at 0.5 on the selected object and duplicate it 5 times"""
    bl_idname = "colmod_01.create_mass_hull"
    bl_label = "Create Mass Hull"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Store the original selection
        original_selection = bpy.context.selected_objects

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Get the active object's name
        active_object_name = bpy.context.active_object.name

        # Iterate through the original selection
        for obj in original_selection:
            # Create a duplicate of the current object
            duplicate = obj.copy()
            duplicate.data = obj.data.copy()
            bpy.context.collection.objects.link(duplicate)
            # Select the duplicate object
            duplicate.select_set(True)
            bpy.context.view_layer.objects.active = duplicate

        # Join all selected objects into a single mesh
        bpy.ops.object.join()

        # Rename the object to the active object name + "_hull"
        bpy.context.active_object.name = active_object_name + "_hull"

        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        # Select all faces
        bpy.ops.mesh.select_all(action='SELECT')
        # Apply the convex hull operator
        bpy.ops.mesh.convex_hull(delete_unused=True, use_existing_faces=False, face_threshold=0.349066, shape_threshold=0)
        # switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the convex hull object
        bpy.context.active_object.select_set(True)

        return {'FINISHED'}
