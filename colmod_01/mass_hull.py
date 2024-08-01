import bpy
import bmesh
from mathutils import Vector
import shutil
import os

class MassHullModifierOperator(bpy.types.Operator):
    """Applies a decimate modifier set to collapse at a user-defined ratio on the selected object and duplicate it 5 times"""
    bl_idname = "colmod_01.create_mass_hull"
    bl_label = "Create Mass Hull"
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
            active_object_name = bpy.context.view_layer.objects.active.name
            new_objects = []

            for obj in original_objects:
                # Create a new object from the selected faces
                selected_faces_verts = self.get_selected_faces_verts(obj)
                if selected_faces_verts:
                    new_obj = self.create_object_from_selected_faces(obj, selected_faces_verts)
                    new_objects.append(new_obj)
                else:
                    self.report({'WARNING'}, f"No faces selected in object: {obj.name}")

            if not new_objects:
                return {'CANCELLED'}

            bpy.ops.object.select_all(action='DESELECT')
            for obj in new_objects:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

        else:
            # Handle object mode selection
            original_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            if not original_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return {'CANCELLED'}

            active_object_name = bpy.context.view_layer.objects.active.name
            bpy.ops.object.select_all(action='DESELECT')

            new_objects = [self.create_object_from_existing(obj) for obj in original_objects]

            for obj in new_objects:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

        # Apply decimation modifier to each new object
        for obj in new_objects:
            decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate_mod.ratio = decimate_ratio
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=decimate_mod.name)

        # Join the decimated objects
        bpy.ops.object.join()

        hull_object = bpy.context.active_object
        hull_object.name = self.get_unique_name(active_object_name)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

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
            if hull_object.data.materials:
                hull_object.data.materials[0] = collision_material
            else:
                hull_object.data.materials.append(collision_material)

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

        new_obj.location = (0, 0, 0)
        new_obj.rotation_euler = (0, 0, 0)
        new_obj.scale = (1, 1, 1)

        return new_obj

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
    bpy.utils.register_class(MassHullModifierOperator)

def unregister():
    bpy.utils.unregister_class(MassHullModifierOperator)

if __name__ == "__main__":
    register()
