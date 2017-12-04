import bpy
import generators
from bpy_extras.io_utils import ExportHelper
import numpy as np
import random
from math import ceil


XML_HEADER = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="{0}mm" height="{1}mm"  viewBox="0 0 {0} {1}" xmlns="http://www.w3.org/2000/svg">
    <title>Sliced Surface</title>
    <desc>Exported Sliced Surface from Blender</desc>
"""
XML_PATH = """<path style="fill:none;stroke:#000000;stroke-width:0.1;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" d="{}"/>
"""
XML_END = "</svg>"

MOVE_COMMAND = 'M{},{} '
LINE_COMMAND = 'L{},{} '
CURVE_COMMAND = 'C{},{} {},{} {},{} '
JOIN_COMMAND = 'Z '


class ExportSlicedSurfaces(bpy.types.Operator, ExportHelper):
    """Export sliced surface as SVG"""
    bl_idname = 'mesh.export_sliced_surface'
    bl_label = 'Export Sliced Surface'
    bl_options = {'PRESET'}
    filename_ext = ".svg"

    @classmethod
    def poll(self, context):
        return (context.mode == 'OBJECT'
                and (context.active_object is not None)
                and (context.active_object.sliced_surface is not None)
                and context.active_object.sliced_surface.sliced_surface)

    def execute(self, context):
        print('export sliced surface')
        prop = context.object.sliced_surface

        xOffset, yOffset = 2, 2

        random.seed(prop.seed)
        surface = generators.SlicedWaveSurfaceGenerator(numWaves=prop.numWaves,
                                                        maxFreq=prop.maxFreq)

        rows = int((prop.canvasHeight - 2*yOffset) / prop.height)
        cols = int((prop.canvasWidth - 2*xOffset) / prop.width)
        rows = min(rows, int(ceil(prop.nSlices / cols)))
        nSlices = min(rows*cols, prop.nSlices)

        paths = []
        for nSlice, u in enumerate(np.linspace(0, 1, nSlices, endpoint=True)):
            row, col = int(nSlice / cols), nSlice % cols

            x0, y0 = xOffset + col*prop.width, yOffset + row*prop.height
            path = ""
            for i, v in enumerate(np.linspace(0, 1, prop.nRes, endpoint=True)):
                x = v*prop.width
                y = surface.getValue(u, v, prop.offset)*prop.amplitude + 0.5*prop.height

                if i == 0:
                    path += MOVE_COMMAND.format((x0 + x), (y0 + y))
                else:
                    path += LINE_COMMAND.format((x0 + x), (y0 + y))
            paths.append(path)

        for row in range(rows + 1):
            path = MOVE_COMMAND.format(xOffset, yOffset + row*prop.height)
            path += LINE_COMMAND.format(xOffset + cols*prop.width, yOffset + row*prop.height)
            paths.append(path)

        for col in range(cols + 1):
            path = MOVE_COMMAND.format(xOffset + col*prop.width, yOffset)
            path += LINE_COMMAND.format(xOffset + col*prop.width, yOffset + rows*prop.height)
            paths.append(path)

        #path = MOVE_COMMAND.format(0, prop.canvasHeight)
        #path += LINE_COMMAND.format(prop.canvasWidth, prop.canvasHeight)
        #paths.append(path)

        print("Export to : " + self.filepath)
        print("{} slices".format(nSlices))
        with open(self.filepath, 'w') as f:
            f.write(XML_HEADER.format(prop.canvasWidth, prop.canvasHeight))
            for path in paths:
                f.write(XML_PATH.format(path))
            f.write(XML_END)

        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)
    print('exportSlicedSurface.py registered')

def unregister():
    bpy.utils.unregister_module(__name__)
    print('exportSlicedSurface.py unregistered')
