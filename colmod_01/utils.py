"""
Shared utilities for COLMOD addon.
Handles material management, naming conventions, and common operations.
"""
import bpy
import os


def get_addon_path():
    """Get the path to the addon directory."""
    return os.path.dirname(os.path.abspath(__file__))


def get_collision_material():
    """
    Get or create the collision material.
    Tries to append from materials.blend first, then creates a fallback.
    """
    material_name = "collision"
    
    # Check if material already exists
    collision_material = bpy.data.materials.get(material_name)
    if collision_material is not None:
        return collision_material
    
    # Try to append from materials.blend
    addon_path = get_addon_path()
    blend_file_path = os.path.join(addon_path, "materials.blend")
    
    if os.path.exists(blend_file_path):
        try:
            # Check if material exists in the blend file
            with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
                if material_name in data_from.materials:
                    data_to.materials = [material_name]
            
            # Try to get the material after appending
            collision_material = bpy.data.materials.get(material_name)
            if collision_material is not None:
                return collision_material
        except Exception:
            pass
    
    # Create fallback material if not found
    return create_fallback_collision_material(material_name)


def create_fallback_collision_material(material_name):
    """Create a simple fallback collision material."""
    collision_material = bpy.data.materials.new(name=material_name)
    collision_material.use_nodes = True
    nodes = collision_material.node_tree.nodes
    
    # Clear default nodes
    for node in nodes:
        nodes.remove(node)
    
    # Create a simple principled BSDF with distinctive color
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.1, 1.0)  # Red color for visibility
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    collision_material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return collision_material


def assign_material(obj, material):
    """Assign a material to an object, replacing the first slot or appending."""
    if material is None:
        return
    
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def get_unique_name(base_name, prefix):
    """
    Generate a unique name for collision objects.
    
    Args:
        base_name: The original object name to base the collision name on
        prefix: The collision prefix (e.g., 'UCX_' for convex, 'UBX_' for box)
    
    Returns:
        A unique name with incrementing suffix
    """
    existing_names = {obj.name for obj in bpy.data.objects}
    counter = 1
    
    while True:
        name = f"{prefix}{base_name}_{counter:02d}"
        if name not in existing_names:
            return name
        counter += 1


def duplicate_object(obj, name_suffix="_copy"):
    """
    Create a duplicate of an object without modifying the original.
    
    Args:
        obj: The object to duplicate
        name_suffix: Suffix to append to the duplicate name
    
    Returns:
        The new duplicated object
    """
    mesh = obj.data.copy()
    new_obj = bpy.data.objects.new(f"{obj.name}{name_suffix}", mesh)
    new_obj.location = obj.location
    new_obj.rotation_euler = obj.rotation_euler
    new_obj.scale = obj.scale
    new_obj.matrix_world = obj.matrix_world
    bpy.context.collection.objects.link(new_obj)
    return new_obj


def duplicate_objects(objects):
    """
    Duplicate multiple objects.
    
    Args:
        objects: List of objects to duplicate
    
    Returns:
        List of duplicated objects
    """
    new_objects = []
    for obj in objects:
        new_obj = duplicate_object(obj)
        new_objects.append(new_obj)
    return new_objects


def ensure_object_mode():
    """Ensure we're in Object Mode, returning the previous mode."""
    previous_mode = bpy.context.mode
    if previous_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return previous_mode


def restore_mode(previous_mode):
    """Restore the previous mode if we changed it."""
    if previous_mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode=previous_mode)
        except RuntimeError:
            pass  # Mode might not be available


def get_selected_mesh_objects():
    """Get all selected mesh objects in the current context."""
    return [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']


def get_active_mesh_object():
    """Get the active mesh object, or None if not a mesh."""
    active_obj = bpy.context.active_object
    if active_obj and active_obj.type == 'MESH':
        return active_obj
    return None


def select_only_objects(objects):
    """Select only the specified objects, deselecting everything else."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def apply_transforms(obj):
    """Apply location, rotation, and scale transforms to an object."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
