import bpy
import bmesh
from mathutils import Vector
import os

class BoundingBoxModifierOperator(bpy.types.Operator):
    """Create a collision box around the selected object or vertices"""
    bl_idname = "colmod_01.create_bounding_box"
    bl_label = "Create Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check for selected objects
        if bpy.context.mode == 'OBJECT':
            selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

            if not selected_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return {'CANCELLED'}

            # Create a duplicate combined object
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = selected_objects[0]
            for obj in selected_objects:
                obj.select_set(True)

            # Duplicate the selection
            bpy.ops.object.duplicate()
            duplicate_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

            # Join the duplicated objects into one
            bpy.context.view_layer.objects.active = duplicate_objects[0]
            bpy.ops.object.join()

            # Apply all transforms to the duplicate object
            duplicate_obj = bpy.context.active_object
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        elif bpy.context.mode == 'EDIT_MESH':
            # In Edit Mode, we should handle vertex selections

            # Switch to Object Mode temporarily
            bpy.ops.object.mode_set(mode='OBJECT')
            active_obj = bpy.context.active_object

            if not active_obj or active_obj.type != 'MESH':
                self.report({'ERROR'}, "Active object is not a mesh.")
                return {'CANCELLED'}

            # Duplicate the active object
            bpy.ops.object.select_all(action='DESELECT')
            active_obj.select_set(True)
            bpy.ops.object.duplicate()
            duplicate_obj = bpy.context.active_object

            # Apply all transforms to the duplicate object
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            # Switch back to Edit Mode to access the selected vertices
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(duplicate_obj.data)

            # Get selected vertices
            vertices = [v.co for v in bm.verts if v.select]
            if not vertices:
                self.report({'ERROR'}, "No vertices selected in edit mode.")
                return {'CANCELLED'}

            min_coords, max_coords = self.calculate_bounding_box_from_vertices(vertices, duplicate_obj)

            # Switch back to Object Mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Delete the duplicate object
            bpy.ops.object.select_all(action='DESELECT')
            duplicate_obj.select_set(True)
            bpy.ops.object.delete()

            # Create the bounding box
            self.create_bounding_box(active_obj, min_coords, max_coords)
            return {'FINISHED'}

        else:
            self.report({'ERROR'}, "Unsupported mode. Please be in Object or Edit Mesh mode.")
            return {'CANCELLED'}

        # Calculate the bounding box based on the duplicate
        min_coords, max_coords = self.calculate_bounding_box(duplicate_obj)

        # Delete the duplicate object
        bpy.ops.object.select_all(action='DESELECT')
        duplicate_obj.select_set(True)
        bpy.ops.object.delete()

        # Create the bounding box
        self.create_bounding_box(selected_objects[0], min_coords, max_coords)

        return {'FINISHED'}

    def calculate_bounding_box(self, obj):
        """Calculate the min and max coordinates of the bounding box for the given object."""
        min_coords = Vector((float('inf'), float('inf'), float('inf')))
        max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))

        # Calculate the bounding box by iterating over each vertex
        for vertex in obj.data.vertices:
            global_coord = obj.matrix_world @ vertex.co
            min_coords.x = min(min_coords.x, global_coord.x)
            min_coords.y = min(min_coords.y, global_coord.y)
            min_coords.z = min(min_coords.z, global_coord.z)
            max_coords.x = max(max_coords.x, global_coord.x)
            max_coords.y = max(max_coords.y, global_coord.y)
            max_coords.z = max(max_coords.z, global_coord.z)

        return min_coords, max_coords

    def calculate_bounding_box_from_vertices(self, vertices, obj):
        """Calculate the min and max coordinates of the bounding box from a list of vertices."""
        min_coords = Vector((float('inf'), float('inf'), float('inf')))
        max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))

        # Calculate the bounding box by iterating over each selected vertex
        for vertex in vertices:
            global_coord = obj.matrix_world @ vertex
            min_coords.x = min(min_coords.x, global_coord.x)
            min_coords.y = min(min_coords.y, global_coord.y)
            min_coords.z = min(min_coords.z, global_coord.z)
            max_coords.x = max(max_coords.x, global_coord.x)
            max_coords.y = max(max_coords.y, global_coord.y)
            max_coords.z = max(max_coords.z, global_coord.z)

        return min_coords, max_coords

    def create_bounding_box(self, original_obj, min_coords, max_coords):
        """Create a bounding box mesh at the specified coordinates."""
        dimensions = max_coords - min_coords
        location = (min_coords + max_coords) * 0.5

        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        bounding_box_obj = bpy.context.active_object
        bounding_box_obj.scale = dimensions  # Adjusted scaling

        # Set the bounding box's name with the specified convention
        base_name = f"UBX_{original_obj.name}_"
        bounding_box_obj.name = self.get_unique_name(base_name)

        # Append and assign the material to the bounding box
        self.append_and_assign_material(bounding_box_obj)

    def get_unique_name(self, base_name):
        """Generate a unique name for the bounding box object by appending an incremental number."""
        count = 1
        unique_name = f"{base_name}{count:02d}"
        while bpy.data.objects.get(unique_name):
            count += 1
            unique_name = f"{base_name}{count:02d}"
        return unique_name

    def append_and_assign_material(self, obj):
        """Append the material from the .blend file and assign it to the object."""
        # Get the addon's path
        addon_path = os.path.dirname(os.path.abspath(__file__))

        # Set the name of the .blend file within the addon folder
        blend_file_name = "materials.blend"

        # Set the name of the material to append
        material_name = "collision"

        # Get the .blend file path
        blend_file_path = os.path.join(addon_path, blend_file_name)

        # Append the material from the .blend file
        if os.path.exists(blend_file_path):
            bpy.ops.wm.append(
                directory=os.path.join(blend_file_path, "Material"),
                filename=material_name,
            )

        # Assign the material to the object
        collision_material = bpy.data.materials.get(material_name)
        if collision_material is not None:
            if obj.data.materials:
                obj.data.materials[0] = collision_material
            else:
                obj.data.materials.append(collision_material)

def register():
    bpy.utils.register_class(BoundingBoxModifierOperator)

def unregister():
    bpy.utils.unregister_class(BoundingBoxModifierOperator)

if __name__ == "__main__":
    register()
