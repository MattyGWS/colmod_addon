import bpy
from bpy.types import Scene
from .mass_hull import MassHullModifierOperator
#from .mass_hull import IndividualHullModifierOperator
#from .mass_hull import BoxModifierOperator
from bpy.types import Panel


bl_info = {
    "name": "colmod_01",
    "author": "Matty Wyett-Simmonds",
    "blender" : (3, 4, 1),
    "version" : (1, 0),
    "location": "View3D > N-Panel > colmod addon",
    "description": "makes collision meshes from selection",
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
        FloatProperty = layout.prop(context.scene, "decimate_ratio")
        layout.separator()
        layout.operator(MassHullModifierOperator.bl_idname, text="Create Mass Hull")
        #layout.operator(IndividualHullModifierOperator.bl_idname, text="Create Individual Hulls")
        #layout.operator(BoxModifierOperator.bl_idname, text="Create Box Collision")


classes = (MassHullModifierOperator, VIEW3D_PT_colmod_object_colmod)
#classes = (IndividualHullModifierOperator, VIEW3D_PT_colmod_object_colmod)
#classes = (BoxModifierOperator, VIEW3D_PT_colmod_object_colmod)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.decimate_ratio = bpy.props.FloatProperty(name="Decimation Ratio", default=0.5, min=0.1, max=0.9)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.decimate_ratio



if __name__ == "__main__":
   register()
