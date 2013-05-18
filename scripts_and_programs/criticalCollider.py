import bpy

bpy.types.Object.collider = bpy.props.StringProperty()       # add a new property, called "foo"
 
class collider(bpy.types.Panel):     # panel to display new property
    bl_space_type = "VIEW_3D"       # show up in: 3d-window
    bl_region_type = "UI"           # show up in: properties panel
    bl_label = "Collider"           # name of the new panel
 
    def draw(self, context):
        # display value of "foo", of the active object
        self.layout.prop(bpy.context.active_object, "collider")
 
bpy.utils.register_class(collider)   # register panel