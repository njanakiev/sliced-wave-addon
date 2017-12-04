import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty
import bmesh
from bpy.app.handlers import persistent
from mathutils import Vector
import random
import numpy as np
import generators


def updateSlicedSurface(self, context):
    obj = context.active_object
    updateSlicedSurfaceObject(obj)

def updateSlicedSurfaceObject(obj):
    mesh = obj.data
    bm = geometry(obj.sliced_surface)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

class SlicedSurfacePropertyGroup(bpy.types.PropertyGroup):
    sliced_surface = BoolProperty(name="Sliced Surface", default=False)

    seed = IntProperty(         name='Seed',
                                description='Seed of random generator',
                                default=0, soft_min=0, soft_max=100,
                                update=updateSlicedSurface)
    nSlices = IntProperty(      name='Number of Slices',
                                description='Number of Slices',
                                default=16, min=2, soft_max=100,
                                update=updateSlicedSurface)
    nRes = IntProperty(         name='Resolution',
                                description='Resolution',
                                default=50, min=2, soft_max=100,
                                update=updateSlicedSurface)
    amplitude = FloatProperty(  name='Amplitude',
                                description='Amplitude of the surface in Z direction',
                                default=64.0, min=0.0, soft_max=1000.0,
                                update=updateSlicedSurface)
    numWaves = IntProperty(     name='Number of Waves',
                                description='Number of Waves',
                                default=5, min=1, soft_max=10,
                                update=updateSlicedSurface)
    maxFreq = IntProperty(      name='Maximum Frequency',
                                description='Maximum frequency of surface',
                                default=1, min=0, soft_max=3,
                                update=updateSlicedSurface)
    sliceDepth = FloatProperty( name='Slice Width',
                                description='Width of each slice',
                                default=1, min=0.1, max=10.0,
                                update=updateSlicedSurface)
    width = FloatProperty(      name='Width',
                                description='Width of slices',
                                default=64.0, min=1.0, soft_max=1000.0,
                                update=updateSlicedSurface)
    height = FloatProperty(     name='Height',
                                description='Height of slices',
                                default=64.0, min=1.0, soft_max=1000.0,
                                update=updateSlicedSurface)
    depth = FloatProperty(      name='Depth',
                                description='Depth of slices',
                                default=64.0, min=1.0, soft_max=1000.0,
                                update=updateSlicedSurface)
    offset = FloatProperty(     name='Offset',
                                description='Offset of generated surface',
                                default=0.0, min=0.0, max=1.0,
                                update=updateSlicedSurface)
    slice = IntProperty(        name='Slice',
                                description='Order of slices',
                                default=0, min=0, soft_max=100,
                                update=updateSlicedSurface)
    canvasWidth = FloatProperty(name='Canvas Width',
                                description='Width of the Canvas for SVG export in meters',
                                default=200.0, min=0.01, soft_max=1.0,
                                update=updateSlicedSurface)
    canvasHeight= FloatProperty(name='Canvas Height',
                                description='Height of the Canvas for SVG export in meters',
                                default=200.0, min=0.01, soft_max=1.0,
                                update=updateSlicedSurface)

def geometry(prop):
    random.seed(prop.seed)
    surface = generators.SlicedWaveSurfaceGenerator(numWaves=prop.numWaves,
                                                    maxFreq=prop.maxFreq)
    bm = bmesh.new()
    scale = 0.1

    sliceDepth = scale*min(prop.sliceDepth, prop.depth / (prop.nSlices - 1))
    uOffset = prop.slice / prop.nSlices

    for nSlice, u0 in enumerate(np.linspace(0,1,prop.nSlices,endpoint=True)):
        x = (u0 - 0.5)*prop.depth - sliceDepth/2
        u = (u0 + uOffset) % 1

        sliceVerts = []
        sliceVerts.append(bm.verts.new((scale*x,  0.5*scale*prop.width, 0.0)))
        sliceVerts.append(bm.verts.new((scale*x, -0.5*scale*prop.width, 0.0)))

        for i, v in enumerate(np.linspace(0, 1, prop.nRes, endpoint=True)):
            y = (v - 0.5)*prop.width
            z = surface.getValue(u, v, prop.offset)*prop.amplitude + 0.5*prop.height
            sliceVerts.append(bm.verts.new((scale*x, scale*y, scale*z)))

        face = bm.faces.new(sliceVerts)

        # Extrude face for each slice
        ret = bmesh.ops.extrude_face_region(bm, geom=[face])
        geom = ret['geom']
        del ret

        faceVerts = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=faceVerts, vec=(sliceDepth, 0.0, 0.0))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    return bm


class SlicedSurface(bpy.types.Operator):
    """Add a sliced surface object to the scene"""
    bl_idname = 'mesh.sliced_surface'
    bl_label = 'Add Sliced Surface'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(self, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # Create mesh and object
        mesh = bpy.data.meshes.new('SlicedSurface')
        obj = bpy.data.objects.new('SlicedSurface', mesh)
        obj.sliced_surface.sliced_surface = True

        # Link object to scene and make it active and selected
        context.scene.objects.link(obj)
        context.scene.update()
        context.scene.objects.active = obj
        obj.select = True

        updateSlicedSurfaceObject(obj)

        return {'FINISHED'}


@persistent
def update_sliced_surfaces(scene):
    #print("update_sliced_surfaces", scene, scene.frame_current)
    for obj in scene.objects:
        if hasattr(obj,'sliced_surface'):
            if obj.sliced_surface.sliced_surface:
                #print(obj)
                updateSlicedSurfaceObject(obj)
    scene.update()

def menu_func(self, context):
    self.layout.operator(SlicedSurface.bl_idname, icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.sliced_surface = bpy.props.PointerProperty(type=SlicedSurfacePropertyGroup)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    bpy.app.handlers.frame_change_post.append(update_sliced_surfaces)
    print('addSlicedSurface.py registered')

def unregister():
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    del bpy.types.Object.sliced_surface
    bpy.app.handlers.frame_change_post.remove(update_sliced_surfaces)
    bpy.utils.unregister_module(__name__)
    print('addSlicedSurface.py unregistered')