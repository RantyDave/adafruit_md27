from cadquery import *
import math

as_mm = 25.4
pcb_thickness = 1.5

class AML27:
    width = 2.5 * as_mm
    height = 2.2 * as_mm
    inset = 0.2 * as_mm
    hole_inset = 0.2 * as_mm
    hole_diameter = 0.1 * as_mm
    edge_round = 0.05 * as_mm
    
    dwidth = 63
    dheight = 43
    dthick = 1.5

    @staticmethod
    def pcb():
        # https://learn.adafruit.com/assets/94078
        return (
            Workplane()
            .box(AML27.width, AML27.height, pcb_thickness, centered=(True, True, False))
            .faces(">Z")
            .rect(AML27.width - AML27.hole_inset, AML27.height - AML27.hole_inset, forConstruction=True)
            .vertices()
            .hole(AML27.hole_diameter)
            .cut(Workplane()
                 .box(AML27.width - AML27.inset * 2, AML27.inset, pcb_thickness, centered=(True, True, False))
                 .translate(Vector(0, -1 * as_mm, 0))
            )
            .edges("|Z")
            .fillet(AML27.edge_round)
        )
    
    @staticmethod
    def lcd():
        return (
            Workplane()
            .box(AML27.dwidth, AML27.dheight, AML27.dthick, centered=(True, True, False))
            .translate((0, 1, 0))
        )
        
    @staticmethod
    def assy():
        return (
            Assembly()
            .add(AML27.pcb(), color=Color(0, 0.5, 0, 0.5))
            .add(AML27.lcd(), color=Color(1, 1, 1, 0.5), loc=Location(Vector(0, 0, pcb_thickness)))
        )


class Mount:
    width = AML27.width + 10
    space_at_bottom = 5
    extension = 40
    pin_height = 4
    side_thick = 4
    col = Color(1, 0.8, 0, 1)
    
    # remember these coordinates are in the YZ plane
    bottom_front =  (-AML27.height / 2 - space_at_bottom, 0)
    end_extension = (-AML27.height / 4                  , -extension)
    top_front =     ( AML27.height / 2                  , 0)
    
    @staticmethod
    def pin(location):
        point = location.Center()
        bottom = Solid.makeCone(AML27.hole_diameter * 0.4, AML27.hole_diameter * 0.5, Mount.pin_height, pnt=point)
        point.z += Mount.pin_height
        top = Solid.makeCone(AML27.hole_diameter * 0.5, AML27.hole_diameter * 0.3, Mount.pin_height / 2, pnt=point)
        return Workplane(bottom).union(top).val()
    
    @staticmethod
    def pins():
        '''Returns pins that dangle underneath a workplane'''
        return (
            Workplane()
            .rect(AML27.width - AML27.hole_inset, AML27.height - AML27.hole_inset, forConstruction=True)
            .vertices()
            .each(Mount.pin)
            .mirror(mirrorPlane="XY")
        )
    
    @staticmethod
    def front():
        return (
            Workplane()
            .box(Mount.width, AML27.height, AML27.dthick, centered=(True, True, False))
            .cut(AML27.lcd())
            .cut(Workplane()
                 .move(0, AML27.height/2)
                 .box(AML27.width * 0.6, 8, 10)
                )
            )
    
    @staticmethod
    def side(right):
        side = (
            Workplane("YZ")
            .moveTo(*Mount.bottom_front)
            .lineTo(*Mount.end_extension).tag("base_rail")
            .lineTo(AML27.height / 2, -AML27.dthick)  # don't clip the top corner
            .lineTo(*Mount.top_front)
            .close()
            .extrude(Mount.side_thick)
            .faces(">X or <X").shell(-Mount.side_thick)
            .edges("|X and (not >>Z[0]) and (not <<Y[0])").fillet(1)
            .edges("|X and <Z").fillet(Mount.side_thick * 1.1)  # extra 10% helps the corner not be kinked
            )

        return side if right else side.mirror(mirrorPlane="YZ")
    
    @staticmethod
    def plate():
        angle = math.atan2(Mount.bottom_front[1] - Mount.end_extension[1],  Mount.end_extension[0] - Mount.bottom_front[0]) * 57.3
        return (
            Workplane("YZ")
            .box(Mount.side_thick * 5, Mount.side_thick * 0.5, Mount.width)
            .rotate((1,0,0), (-1,0,0), angle)
            )
    
    @staticmethod
    def assy():
        plate_attached = Vector(0, ((Mount.bottom_front[0] + Mount.end_extension[0]) / 2) + Mount.side_thick , -Mount.extension / 2)
        return (
            Assembly()
            .add(Mount.front(),     loc=Location(Vector(0, 0, pcb_thickness)),                                  color=Mount.col)
            .add(Mount.pins(),      loc=Location(Vector(0, 0, pcb_thickness)),                                  color=Mount.col)
            .add(Mount.side(False), loc=Location(Vector( Mount.width / 2, 0, pcb_thickness + AML27.dthick)),    color=Mount.col)
            .add(Mount.side(True),  loc=Location(Vector(-Mount.width / 2, 0, pcb_thickness + AML27.dthick)),    color=Mount.col)
            .add(Mount.plate(),     loc=Location(plate_attached),                                               color=Mount.col)
        )
        


Mount.assy().save("adafruit_md.step")
show_object(Assembly().add(AML27.assy()).add(Mount.assy()))

