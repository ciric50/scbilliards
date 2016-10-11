# Written for Blender 2.77a
#

import copy
import logging
import csv
import operator
import math

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
        self.show_xlo = True
        self.show_xhi = True
        self.show_ylo = True
        self.show_yhi = True
        self.show_zlo = True
        self.show_zhi = True

        self.np = 0   # Number of particles
        self.box_size = 4.0
        self.default_r = 0.1

#-----------------------------------------------------------------------------

class Collision:
    def __init__(self, index, t, xyz, angles):
        self.index = index
        self.t = t
        self.xyz = xyz
        self.angles = angles

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
    '''
    if params.show_xlo:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-xlo'
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler = (0, 0.5*math.pi, 0)
        ob.location = (-params.box_size, 0, 0)
        ob.scale = (params.box_size, params.box_size, params.box_size)
    if params.show_xhi:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-xhi'
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler = (0, 0.5*math.pi, 0)
        ob.location = (params.box_size, 0, 0)
        ob.scale = (params.box_size, params.box_size, params.box_size)

    if params.show_ylo:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-ylo'
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler = (0.5*math.pi, 0, 0)
        ob.location = (0, -params.box_size, 0)
        ob.scale = (params.box_size, params.box_size, params.box_size)
    if params.show_yhi:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-yhi'
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler = (0.5*math.pi, 0, 0)
        ob.location = (0, params.box_size, 0)
        ob.scale = (params.box_size, params.box_size, params.box_size)

    if params.show_zlo:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-zlo'
        ob.location = (0, 0, -params.box_size)
        ob.scale = (params.box_size, params.box_size, params.box_size)
    if params.show_zhi:
        bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.scene.objects.active
        ob.name = 'wall-zhi'
        ob.location = (0, 0, params.box_size)
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
                t = float(row[3])
                index = int(float(row[1]))
                xyz = [float(row[4]), float(row[5]), float(row[6])]
                angles = [float(row[7]), float(row[8]), float(row[9])]
                coll = Collision(index, t, xyz, angles)
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
        ob = oblist[-1]
        ob.name = "sphere."+str(k).zfill(4)
        ob.rotation_mode = 'XYZ'
        for poly in ob.data.polygons:
            poly.use_smooth = True

    # Set keyframes for each collision
    for coll in clist:
        # Set the current frame
        frame_num = t2frame(coll.t, params.time_scale)
        bpy.context.scene.frame_current = frame_num

        # Set the sphere location and size at this keyframe
        ob = oblist[coll.index]
        ob.rotation_euler = tuple(coll.angles)
        ob.location = tuple(coll.xyz)
        r = radii[coll.index]
        ob.scale = (r,r,r)

        # Insert the keyframes
        ob.keyframe_insert('location', frame=frame_num)
        ob.keyframe_insert('rotation_euler', frame=frame_num)

    # Use linear interpolation between keyframes
    for ob in oblist:
        for fcurve in ob.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    # Add the surrounding box
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

    show_xlo = BoolProperty(name="Show box xlo", default=True, description="Show the xlo box face?")
    show_xhi = BoolProperty(name="Show box xhi", default=False, description="Show the xhi box face?")
    show_ylo = BoolProperty(name="Show box ylo", default=False, description="Show the ylo box face?")
    show_yhi = BoolProperty(name="Show box yhi", default=True, description="Show the yhi box face?")
    show_zlo = BoolProperty(name="Show box zlo", default=True, description="Show the zlo box face?")
    show_zhi = BoolProperty(name="Show box zhi", default=False, description="Show the zhi box face?")

    def execute(self, context):
        # Set cycles render engine if not selected
        scn = bpy.context.scene
        if not scn.render.engine == 'CYCLES':
            scn.render.engine = 'CYCLES'

        params = BilliardParams()

        params.initfile = self.initfile
        params.time_scale = self.time_scale
        params.show_xlo = self.show_xlo
        params.show_xhi = self.show_xhi
        params.show_ylo = self.show_ylo
        params.show_yhi = self.show_yhi
        params.show_zlo = self.show_zlo
        params.show_zhi = self.show_zhi

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
