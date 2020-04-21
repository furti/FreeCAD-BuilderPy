import FreeCAD
import Part
import Sketcher
from AbstractBuilder import AbstractBuilder, AbstractFeature

ORIGIN_INDEX = (-1, 1)


class SketchBuilder(AbstractBuilder):
    def __init__(self, start_x=0, start_y=0):
        super().__init__("Sketcher::SketchObject")

        self.move(start_x, start_y)

    def move(self, x=0, y=0):
        self.addFeature(MoveFeature(x, y))

        return self

    def line(self, add_x, add_y):
        return self.addFeature(LineFeature(add_x, add_y))

    def horizontal_line(self, add_x, constraint_distance=True):
        line = self.line(add_x, 0).horizontal()

        if constraint_distance:
            line = line.distance_x(add_x)

        return line

    def vertical_line(self, add_y, constraint_distance=True):
        line = self.line(0, add_y).vertical()

        if constraint_distance:
            line = line.distance_y(add_y)

        return line

    def bspline(self):
        return self.addFeature(BsplineFeature(self))

    def build_context(self):
        return SketchBuilderContext()

    def cleanup_object(self, sketch):
        sketch.deleteAllConstraints()
        sketch.deleteAllGeometry()


class SketchBuilderContext:
    def __init__(self):
        print("Setting Up Sketcher Context")
        self.actualPoint = FreeCAD.Vector(0, 0)
        self.geometry_index = -1

    def move(self, x, y):
        self.actualPoint = FreeCAD.Vector(x, y)

    def add(self, vector):
        start = FreeCAD.Vector(self.actualPoint.x, self.actualPoint.y)
        end = self.actualPoint.add(vector)

        self.actualPoint = end

        return (start, end)

    def geometry_added(self):
        self.geometry_index += 1

        print("At Gemometry index %s" % (self.geometry_index, ))

        return self.geometry_index


class AbstractSketchBuilderFeature(AbstractFeature):
    def __init__(self):
        super().__init__()

        self.constraints = []
        self.construction_geometry = False
        self.geometry_index = 0

    def construction(self):
        self.construction_geometry = True

        return self

    def horizontal(self):
        self.constraints.append(HorizontalConstraint())

        return self

    def vertical(self):
        self.constraints.append(VerticalConstraint())

        return self

    def symmetricToOrigin(self):
        self.constraints.append(SymmetryConstraint(ORIGIN_INDEX))

        return self

    def distance_x(self, distance):
        self.constraints.append(DistanceConstraint(distance, "DistanceX"))

        return self

    def distance_y(self, distance):
        self.constraints.append(DistanceConstraint(distance, "DistanceY"))

        return self

    def coincidentToOrigin(self):
        self.constraints.append(CoincidentConstraint(ORIGIN_INDEX))

        return self

    def coincident(self, feature, point_index):
        self.constraints.append(
            CoincidentConstraint((feature, point_index), True))

        return self

    def geometry_added(self, context):
        self.geometry_index = context.geometry_added()

    def apply(self, sketch, context):
        if self.construction_geometry:
            sketch.toggleConstruction(context.geometry_index)


class MoveFeature(AbstractFeature):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def append(self, sketch, context):
        context.move(self.x, self.y)


class LineFeature(AbstractSketchBuilderFeature):
    def __init__(self, add_x, add_y):
        super().__init__()

        self.to_add = FreeCAD.Vector(add_x, add_y)

    def append(self, sketch, context):
        start, end = context.add(self.to_add)

        sketch.addGeometry(Part.LineSegment(start, end))
        self.geometry_added(context)

        for constraint in self.constraints:
            constraint.apply(sketch, (context.geometry_index,
                                      1), (context.geometry_index, 2))

        self.apply(sketch, context)


class BsplineFeature(AbstractSketchBuilderFeature):
    def __init__(self, builder):
        super().__init__()

        self.builder = builder
        self.circles = []

    def point(self, x, y):
        circle = CircleFeature(x, y, 10).constraint_radius().construction()

        self.circles.append(circle)

        return circle

    def append(self, sketch, context):
        vector_list = []
        for circle in self.circles:
            circle.append(sketch, context)
            vector_list.append(circle.point)

        sketch.addGeometry(Part.BSplineCurve(
            vector_list, None, None, False, 3, None, False))

        self.geometry_added(context)


class CircleFeature(AbstractSketchBuilderFeature):
    def __init__(self, x, y, radius):
        super().__init__()

        self.point = FreeCAD.Vector(x, y)
        self.radius = radius

    def constraint_radius(self):
        self.constraints.append(RadiusConstraint(self.radius))

        return self

    def append(self, sketch, context):
        sketch.addGeometry(Part.Circle(
            self.point, FreeCAD.Vector(0, 0, 1), self.radius))
        self.geometry_added(context)

        for constraint in self.constraints:
            constraint.apply(sketch, (context.geometry_index, 3), None)

        self.apply(sketch, context)


class HorizontalConstraint:
    def __init__(self):
        pass

    def apply(self, sketch, idx1, idx2):
        print("Horizontal: %s, %s, %s, %s" %
              (idx1[0], idx1[1], idx2[0], idx2[1]))

        sketch.addConstraint(Sketcher.Constraint(
            'Horizontal', idx1[0], idx1[1], idx2[0], idx2[1]))


class VerticalConstraint:
    def __init__(self):
        pass

    def apply(self, sketch, idx1, idx2):
        print("Vertical: %s, %s, %s, %s" %
              (idx1[0], idx1[1], idx2[0], idx2[1]))

        sketch.addConstraint(Sketcher.Constraint(
            'Vertical', idx1[0], idx1[1], idx2[0], idx2[1]))


class SymmetryConstraint:
    def __init__(self, point):
        self.point = point

    def apply(self, sketch, idx1, idx2):
        sketch.addConstraint(Sketcher.Constraint(
            'Symmetric', idx1[0], idx1[1], idx2[0], idx2[1], self.point[0], self.point[1]))


class CoincidentConstraint:
    def __init__(self, point, is_feature=False):
        self.point = point
        self.is_feature = is_feature

    def apply(self, sketch, idx1, idx2):
        point = self.point

        if self.is_feature:
            feature = self.point[0]
            feature_index = feature.geometry_index

            point = (feature_index, self.point[1])

        print("Coincident: %s, %s, %s, %s" %
              (point[0], point[1], idx1[0], idx1[1]))

        sketch.addConstraint(Sketcher.Constraint(
            'Coincident', point[0], point[1], idx1[0], idx1[1]))


class DistanceConstraint:
    def __init__(self, distance, distance_type):
        self.distance = distance
        self.distance_type = distance_type

    def apply(self, sketch, idx1, idx2):
        sketch.addConstraint(Sketcher.Constraint(
            self.distance_type, idx1[0], idx1[1], idx2[0], idx2[1], self.distance))


class RadiusConstraint:
    def __init__(self, radius):
        self.radius = radius

    def apply(self, sketch, idx1, idx2):
        sketch.addConstraint(Sketcher.Constraint(
            'Radius', idx1[0], self.radius))


if __name__ == "__main__":
    if FreeCAD.ActiveDocument is None:
        print("Create a document to continue.")
    else:
        base_length = 180
        base_height = 65
        half_base_length = base_length / 2
        bending_width = 61.5

        builder = SketchBuilder(-half_base_length, 0)
        horizontal_construction_line = builder.horizontal_line(
            base_length).symmetricToOrigin().construction()
        vertical_construction_line = builder.move(0, 0).vertical_line(
            base_height).coincidentToOrigin().construction()

        bspline = builder.bspline()
        bspline.point(-half_base_length,
                      0).coincident(horizontal_construction_line, 1)
        bspline.point(-bending_width, base_height)
        bspline.point(0, base_height).coincident(vertical_construction_line, 2)
        bspline.point(bending_width, base_height)
        bspline.point(half_base_length, 0).coincident(
            horizontal_construction_line, 2)

        sketch = builder.build("TestSketch")
