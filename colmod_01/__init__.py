import bpy
from bpy.types import Scene, Panel
from .mass_hull import MassHullModifierOperator
from .individual_hull import IndividualHullModifierOperator
from .bounding_box import BoundingBoxModifierOperator

bl_info = {
    "name": "COLMOD - Collision Mesh Generator",
    "author": "Matty Wyett-Simmonds",
    "blender" : (5, 1, 0),
    "version" : (1, 1, 0),
    "location": "View3D > N-Panel > COLMOD",
    "description": "Creates collision meshes (convex hulls, boxes) from selected objects or faces for game engines like Unreal",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

class VIEW3D_PT_colmod_object_colmod(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "COLMOD Settings"
    bl_category = "COLMOD"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Decimation ratio slider
        layout.prop(scene, "colmod_decimate_ratio", text="Decimation Ratio")
        layout.separator()
        
        # Collision creation buttons
        layout.operator(MassHullModifierOperator.bl_idname, text="Create Mass Hull")
        layout.operator(IndividualHullModifierOperator.bl_idname, text="Create Individual Hulls")
        layout.operator(BoundingBoxModifierOperator.bl_idname, text="Create Box Collision")

classes = (
    MassHullModifierOperator,
    IndividualHullModifierOperator,
    BoundingBoxModifierOperator,
    VIEW3D_PT_colmod_object_colmod,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register scene properties
    bpy.types.Scene.colmod_decimate_ratio = bpy.props.FloatProperty(
        name="Decimation Ratio",
        default=0.5,
        min=0.01,
        max=1.0,
        description="Ratio for decimation modifier (lower = more simplified)"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Clean up scene properties
    if hasattr(bpy.types.Scene, 'colmod_decimate_ratio'):
        del bpy.types.Scene.colmod_decimate_ratio

if __name__ == "__main__":
    register()
