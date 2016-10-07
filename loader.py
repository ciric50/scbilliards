# Written for Blender 2.77a
#

import copy
import logging
import csv
import operator

import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty
from bpy.props import IntProperty, EnumProperty, StringProperty

#-----------------------------------------------------------------------------

class BilliardParams():
    '''
    Parameters used for billiard animations.
    '''
    def __init__(self):
        self.initfile = None
        self.time_scale = 24.0
        self.show_box = False

        self.np = 0   # Number of particles
        self.box_size = 4.0
        self.default_r = 0.1

#-----------------------------------------------------------------------------

class Collision:
    def __init__(self, index, t, xyz):
        self.index = index
        self.t = t
        self.xyz = xyz

#-----------------------------------------------------------------------------

def t2frame(t, tscale):
    '''
    Convert simulation time to a frame number.

    Arguments:
        t - time to be converted
        tscale - time scaling factor

    Returns the corresponding frame number.
    '''
    return int(t * tscale) + 1

#-----------------------------------------------------------------------------

def add_box(params):
    '''
    Add the box object enclosing the simulation particles.

    Arguments:
        params - BilliardParams object with parameters to use

    Returns the corresponding frame number.
    '''
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.scene.objects.active
    ob.scale = (params.box_size, params.box_size, params.box_size)

#-----------------------------------------------------------------------------

def load_billiard_data(params):
    '''
    Run the shape grammar.

    Arguments:
        params - BilliardParams object with parameters to use
    '''
    if params.initfile == None or params.initfile == '':
        return
    with open(params.initfile, "r") as csvfile:
        rd = csv.reader(csvfile, delimiter=',')
        rspec = {}
        clist = []

        # Read in the csv file, one line at a time
        for row in rd:
            # Skip comments and empty lines
            if row == None or row == '' or row[0][0] == '#':
                continue

            if row[0] == 'box':
                b = float(row[1])
            elif row[0] == 'default-radius':
                params.default_r = float(row[1])
            elif row[0] == 'r':
                index = int(float(row[1]))
                rspec[index] = float(row[2])
            elif row[0] == 'c':
                t = float(row[1])
                index = int(float(row[2]))
                xyz = [float(row[3]), float(row[4]), float(row[5])]
                coll = Collision(index, t, xyz)
                clist.append(coll)

    # Now we have the data from the file. Find the number
    # of particles by determining the max index.
    m = max(clist, key=operator.attrgetter('index'))
    np = m.index + 1

    # Set the particle radii
    radii = [params.default_r for k in range(np)]
    for ix in rspec:
        radii[ix] = rspec[ix]

    # Insert the spheres and make a list of these objects by index
    oblist = []
    for k in range(np):
        #bpy.ops.mesh.primitive_ico_sphere_add()
        bpy.ops.mesh.primitive_uv_sphere_add()
        oblist.append(bpy.context.scene.objects.active)
        oblist[-1].name = "sphere."+str(k).zfill(4)
        for poly in oblist[-1].data.polygons:
            poly.use_smooth = True

    # Set keyframes for each collision
    for coll in clist:
        # Set the current frame
        frame_num = t2frame(coll.t, params.time_scale)
        bpy.context.scene.frame_current = frame_num

        # Set the sphere location and size at this keyframe
        ob = oblist[coll.index]
        ob.location = tuple(coll.xyz)
        r = radii[coll.index]
        ob.scale = (r,r,r)

        # Insert the keyframe
        ob.keyframe_insert('location', frame=frame_num)

    # Use linear interpolation between keyframes
    for ob in oblist:
        for fcurve in ob.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    # Add the surrounding box
    if params.show_box:
        add_box(params)

#-----------------------------------------------------------------------------

class BilliardsOperator(bpy.types.Operator):
    ''' Billiards '''
    bl_idname = "mesh.scbilliards"
    bl_label = "Billiards Operator"
    bl_options = {'REGISTER', 'UNDO'}

    initfile = StringProperty(
        name="Initial Shapes Filename",
        description="Filename containing initialization data",
        subtype="FILE_PATH",
        default=""
    )

    time_scale = FloatProperty(
        name="Time scale",
        default=24.0
    )

    show_box = BoolProperty(name="Show box", default=False, description="Show the enclosing box?")

    def execute(self, context):
        # Set cycles render engine if not selected
        scn = bpy.context.scene
        if not scn.render.engine == 'CYCLES':
            scn.render.engine = 'CYCLES'

        params = BilliardParams()

        params.initfile = self.initfile
        params.time_scale = self.time_scale
        params.show_box = self.show_box

        load_billiard_data(params)

        return {'FINISHED'}
 
#-----------------------------------------------------------------------------

def add_object_button(self, context):
    self.layout.operator(
        BilliardsOperator.bl_idname,
        text=BilliardsOperator.__doc__,
        icon='PLUGIN')

def register():
    bpy.utils.register_class(BilliardsOperator)
    bpy.types.INFO_MT_add.append(add_object_button)
