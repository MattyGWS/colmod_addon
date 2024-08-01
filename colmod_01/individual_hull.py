import bpy
import bmesh
from mathutils import Vector
import shutil
import os

class IndividualHullModifierOperator(bpy.types.Operator):
    """Creates individual convex hulls around selected objects or groups of selected faces."""
    bl_idname = "colmod_01.create_individual_hull"
    bl_label = "Create Individual Hull"
    bl_options = {'REGISTER', 'UNDO'}

    def create_object_from_existing(self, obj):
        mesh = obj.data.copy()
        new_obj = bpy.data.objects.new(obj.name + "_copy", mesh)
        new_obj.location = obj.location
        new_obj.rotation_euler = obj.rotation_euler
        new_obj.scale = obj.scale
        bpy.context.collection.objects.link(new_obj)
        return new_obj

    def execute(self, context):
        decimate_ratio = context.scene.decimate_ratio

        if bpy.context.mode == 'EDIT_MESH':
            # Handle edit mode selection
            bpy.ops.object.mode_set(mode='OBJECT')
            original_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

            for obj in original_objects:
                selected_faces_verts = self.get_selected_faces_verts(obj)
                if selected_faces_verts:
                    new_obj = self.create_object_from_selected_faces(obj, selected_faces_verts)
                    self.apply_convex_hull_and_decimate(new_obj, decimate_ratio)
                else:
                    self.report({'WARNING'}, f"No faces selected in object: {obj.name}")

        else:
            # Handle object mode selection
            original_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            if not original_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return {'CANCELLED'}

            for obj in original_objects:
                new_obj = self.create_object_from_existing(obj)
                self.apply_convex_hull_and_decimate(new_obj, decimate_ratio)

        return {'FINISHED'}

    def get_selected_faces_verts(self, obj):
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        selected_verts = []
        if bm.faces:
            for face in bm.faces:
                if face.select:
                    for vert in face.verts:
                        selected_verts.append(obj.matrix_world @ vert.co)
        bm.free()
        return selected_verts

    def create_object_from_selected_faces(self, obj, selected_verts):
        # Create a new mesh object from the selected vertices
        mesh = bpy.data.meshes.new(obj.name + "_selected_faces")
        new_obj = bpy.data.objects.new(obj.name + "_selected_faces", mesh)
        bpy.context.collection.objects.link(new_obj)

        bm = bmesh.new()
        for vert in selected_verts:
            bm.verts.new(vert)
        bm.verts.ensure_lookup_table()
        bmesh.ops.convex_hull(bm, input=bm.verts)
        bm.to_mesh(mesh)
        bm.free()

        new_obj.location = obj.location
        new_obj.rotation_euler = obj.rotation_euler
        new_obj.scale = obj.scale

        return new_obj

    def apply_convex_hull_and_decimate(self, obj, decimate_ratio):
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Apply convex hull
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply decimation modifier
        decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate_mod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier=decimate_mod.name)

        # Rename the object with the unique name
        obj.name = self.get_unique_name(obj.name)

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

        # Assign the material to the hull object
        collision_material = bpy.data.materials.get(material_name)
        if collision_material is not None:
            if obj.data.materials:
                obj.data.materials[0] = collision_material
            else:
                obj.data.materials.append(collision_material)

    def get_unique_name(self, base_name):
        prefix = "UCX_"
        suffix = "_01"
        name = prefix + base_name + suffix

        existing_names = {obj.name for obj in bpy.data.objects}
        counter = 1
        while name in existing_names:
            counter += 1
            suffix = f"_{counter:02d}"
            name = prefix + base_name + suffix

        return name

def register():
    bpy.utils.register_class(IndividualHullModifierOperator)

def unregister():
    bpy.utils.unregister_class(IndividualHullModifierOperator)

if __name__ == "__main__":
    register()
